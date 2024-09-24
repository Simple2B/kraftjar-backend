import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import app.models as m
import app.schema as s
from typing import Sequence, cast
from api.dependency import get_current_user
from app.database import get_db
from app.logger import log
import api.controllers as c

application_router = APIRouter(prefix="/applications", tags=["applications"])


@application_router.get("/{application_id}", status_code=status.HTTP_200_OK, response_model=s.ApplicationOut)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    application: m.Application | None = db.scalar(sa.select(m.Application).where(m.Application.id == application_id))
    if not application:
        log(log.ERROR, "Application [%s] not found", application_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return application


@application_router.get("/", status_code=status.HTTP_200_OK, response_model=s.ApplicationOutList)
def get_applications(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    query = (
        sa.select(m.Application)
        .join(m.Job, sa.or_(m.Application.worker_id == current_user.id, m.Job.owner_id == current_user.id))
        .filter(m.Application.job_id == m.Job.id)
    )

    applications: Sequence[m.Application] = db.scalars(query).all()
    return s.ApplicationOutList(data=cast(list, applications))


@application_router.post("/", status_code=status.HTTP_201_CREATED, response_model=s.ApplicationOut)
def create_application(
    data: s.ApplicationIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    job: m.Job | None = db.scalar(sa.select(m.Job).where(m.Job.id == data.job_id))
    if not job:
        log(log.ERROR, "Job [%s] not found", data.job_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    worker: m.User | None = db.scalar(sa.select(m.User).where(m.User.id == data.worker_id))
    if not worker:
        log(log.ERROR, "Worker [%s] not found", data.worker_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    if job.owner_id == data.worker_id:
        log(log.ERROR, "User [%s] is not allowed to create application", current_user.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not allowed to create application")

    # worker can't invite himself
    is_worker_inviting = current_user.id == data.worker_id and data.type == m.ApplicationType.INVITE
    # owner can't apply to his job
    is_owner_applying = current_user.id == job.owner_id and data.type == m.ApplicationType.APPLY

    if any([is_worker_inviting, is_owner_applying]):
        log(log.ERROR, "User [%s] is not allowed to create application with such type", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User is not allowed to create application with such type"
        )

    application: m.Application = m.Application(
        worker_id=data.worker_id,
        job_id=job.id,
        type=data.type,
    )
    db.add(application)
    db.commit()
    log(log.INFO, "Created application [%s] for job [%s]", application.id, job.id)
    return application


@application_router.put("/{application_id}", status_code=status.HTTP_200_OK, response_model=s.ApplicationPutOut)
def update_application(
    application_id: int,
    data: s.ApplicationPutIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    if not data.status:
        log(log.ERROR, "Status is required")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status is required")

    application: m.Application | None = db.scalar(sa.select(m.Application).where(m.Application.id == application_id))

    if not application:
        log(log.ERROR, "Application [%s] not found", application_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if application.status in [m.ApplicationStatus.ACCEPTED, m.ApplicationStatus.REJECTED]:
        log(log.ERROR, "Application [%s] is already completed", application_id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Application is already completed")

    job_owner_id: int | None = db.scalar(sa.select(m.Job.owner_id).where(m.Job.id == application.job_id))
    if not job_owner_id:
        log(log.ERROR, "Job [%s] not found", application.job_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Check permissions
    is_update_not_allowed = current_user.id not in [job_owner_id, application.worker_id]
    # worker can't update application
    is_worker_not_allowed_to_update = (
        current_user.id == application.worker_id and application.type == m.ApplicationType.APPLY
    )
    # owner can't update application
    is_owner_not_allowed_to_update = current_user.id == job_owner_id and application.type == m.ApplicationType.INVITE

    if any([is_update_not_allowed, is_worker_not_allowed_to_update, is_owner_not_allowed_to_update]):
        log(log.ERROR, "User [%s] is not allowed to update application [%s]", current_user.id, application.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not allowed to update application")

    db.execute(sa.update(m.Application).where(m.Application.id == application_id).values(status=data.status))
    log(log.INFO, "Updated application [%s] with status: [%s]", application_id, data.status.name)

    if data.status == m.ApplicationStatus.ACCEPTED:
        c.reject_applications(db, application)

        db.execute(sa.update(m.Job).where(m.Job.id == application.job_id).values(status=s.JobStatus.IN_PROGRESS.value))
        log(log.INFO, "Updated job [%s] status to IN_PROGRESS", application.job_id)

    db.commit()
    log(log.INFO, "Successfully updated application [%s]", application_id)

    return s.ApplicationPutOut(application=application)
