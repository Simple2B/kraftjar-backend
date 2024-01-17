from typing import Sequence, cast, Any

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

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
    current_user: m.User | None = Depends(get_user),
):
    query = sa.select(m.Job)
    if current_user:
        query = query.where(m.Job.user_id == current_user.id)
    jobs: Sequence[m.Job] = db.scalars(query).all()
    return s.JobOutList(jobs=cast(list, jobs))


@job_router.post("/", status_code=status.HTTP_201_CREATED, response_model=s.JobOut)
def create_job(
    job: s.JobIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    new_job: m.Job = m.Job(
        **job.model_dump(),
        owner_id=current_user.id,
    )
    db.add(new_job)
    db.commit()
    log(log.INFO, "Created job [%s] for user [%s]", new_job.title, new_job.owner_id)
    return job


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
