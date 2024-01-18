import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import app.models as m
import app.schema as s
from typing import Sequence, cast, Any
from api.dependency import get_current_user
from app.database import get_db
from app.logger import log

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

    if job.owner_id == data.worker_id:
        log(log.ERROR, "User [%s] is not allowed to create application", current_user.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not allowed to create application")

    if any(
        [
            current_user.id == data.worker_id and data.type == m.ApplicationType.INVITE,
            current_user.id == job.owner_id and data.type == m.ApplicationType.APPLY,
        ]
    ):
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


@application_router.put("/{application_id}", status_code=status.HTTP_200_OK, response_model=s.ApplicationOut)
def update_application(
    application_id: int,
    data: s.ApplicationPut,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    application: m.Application | None = db.scalar(sa.select(m.Application).where(m.Application.id == application_id))

    if not application:
        log(log.ERROR, "Application [%s] not found", application_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    job_owner_id: m.User | None = db.scalar(sa.select(m.Job.owner_id).where(m.Job.id == application.job_id))
    if not job_owner_id:
        log(log.ERROR, "Job [%s] not found", application.job_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if any(
        [
            current_user.id not in [job_owner_id, application.worker_id],
            current_user.id == application.worker_id and application.type == m.ApplicationType.APPLY,
            current_user.id == job_owner_id and application.type == m.ApplicationType.INVITE,
        ]
    ):
        log(log.ERROR, "User [%s] is not allowed to update application [%s]", current_user.id, application.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not allowed to update application")

    data_filtered: dict[str, Any] = {k: v for k, v in data.model_dump().items() if v is not None}

    db.execute(sa.update(m.Application).where(m.Application.id == application_id).values(**data_filtered))
    db.commit()
    log(log.INFO, "Updated job [%s]", application_id)

    return application
