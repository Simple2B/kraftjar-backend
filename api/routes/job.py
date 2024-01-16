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
    job: m.Job = db.scalar(sa.select(m.Job).where(m.Job.id == job_id))
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
    jobs: list[m.Job] = db.scalars(query).all()
    return s.JobOutList(jobs=jobs)


@job_router.post("/", status_code=status.HTTP_201_CREATED, response_model=s.JobOut)
def create_job(
    job: s.JobIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    pass


@job_router.put("/{job_id}", status_code=status.HTTP_200_OK, response_model=s.JobOut)
def update_job(
    job_id: int,
    job: s.JobIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    pass
