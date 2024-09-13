from datetime import datetime
from typing import Sequence, cast, Any

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import api.controllers as c
from api.controllers.job import job_statistics
import app.models as m
import app.schema as s
from api.dependency import get_current_user, get_user
from app.database import get_db
from app.logger import log

job_router = APIRouter(prefix="/jobs", tags=["jobs"])


@job_router.get("/{job_id}", status_code=status.HTTP_200_OK, response_model=s.JobOut)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: m.User | None = Depends(get_user),
):
    job: m.Job | None = db.scalar(sa.select(m.Job).where(m.Job.id == job_id))
    if not job:
        log(log.ERROR, "Job [%s] not found", job_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@job_router.get("/", status_code=status.HTTP_200_OK, response_model=s.JobOutList)
def get_jobs(
    db: Session = Depends(get_db),
    # get cur_user
    current_user: m.User | None = Depends(get_user),
):
    query = sa.select(m.Job)
    if current_user:
        query = query.where(m.Job.user_id == current_user.id)
    jobs: Sequence[m.Job] = db.scalars(query).all()
    return s.JobOutList(jobs=cast(list, jobs))


@job_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.JobOut,
    responses={
        status.HTTP_409_CONFLICT: {"description": "Selected service not found"},
    },
)
def create_job(
    job: s.JobIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    if job.service_uuid:
        service = db.scalar(sa.select(m.Service).where(m.Service.uuid == job.service_uuid))
        if not service:
            log(log.ERROR, "Service [%s] not found", job.service_uuid)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Selected service not found")

    if job.location_uuid:
        location = db.scalar(sa.select(m.Location).where(m.Location.uuid == job.location_uuid))
        if not location:
            log(log.ERROR, "Location [%s] not found", job.location_uuid)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Selected location not found")

    new_job: m.Job = m.Job(
        **job.model_dump(exclude={"service_uuid", "location_uuid", "start_date", "end_date"}),
        owner_id=current_user.id,
        location_id=location.id if location else None,
        start_date=datetime.fromisoformat(job.start_date) if job.start_date else None,
        end_date=datetime.fromisoformat(job.end_date) if job.end_date else None,
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    log(log.INFO, "Created job [%s] for user [%s]", new_job.title, new_job.owner_id)

    job_services = m.JobService(
        job_id=new_job.id,
        service_id=job.service_uuid,
    )
    db.add(job_services)
    db.commit()
    db.refresh(job_services)

    return new_job


@job_router.put("/{job_id}", status_code=status.HTTP_200_OK, response_model=s.JobOut)
def put_job(
    job_id: int,
    job_data: s.JobPut,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    job: m.Job | None = db.scalar(sa.select(m.Job).where(m.Job.id == job_id))
    if not job:
        log(log.ERROR, "Job [%s] not found", job_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.owner_id != current_user.id:
        log(log.ERROR, "User [%s] does not own job [%s]", current_user.id, job_id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not own job")

    data_filtered: dict[str, Any] = {key: value for key, value in job_data.model_dump().items() if value is not None}

    db.execute(sa.update(m.Job).where(m.Job.id == job_id).values(**data_filtered))
    db.commit()
    log(log.INFO, "Updated job [%s]", job_id)
    return job


@job_router.post("/search", status_code=status.HTTP_200_OK, response_model=s.JobsSearchOut)
def search_jobs(
    query: s.JobSearchIn,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    responses={
        status.HTTP_409_CONFLICT: {"description": "Selected service not found"},
    },
):
    """Returns filtered list of jobs"""
    return c.search_jobs(query, current_user, db)


@job_router.post("/home", status_code=status.HTTP_200_OK, response_model=s.JobsCardList)
def get_jobs_on_home_page(
    query: s.JobHomePage,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Returns jobs for home page"""
    return c.get_jobs_on_home_page(query, current_user, db)


@job_router.get("/public-job-statistics/", status_code=status.HTTP_200_OK, response_model=s.PublicJobDict)
def get_public_job_statistics(
    db: Session = Depends(get_db),
):
    """Get statistics for jobs per location"""

    return job_statistics(db)
