import random
from typing import Sequence

from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models as m
from app.logger import log


faker: Faker = Faker()

APPLICATIONS_COUNT = 5


def create_applications(db: Session, count: int = APPLICATIONS_COUNT):
    """Creates applications for each Pending job

    Args:
        db (Session): Database session
        count (int, optional): Number of applications to create. Defaults to APPLICATIONS_COUNT.
    """
    types: list = list(m.ApplicationType)
    jobs: Sequence[m.Job] = db.scalars(select(m.Job).where(m.Job.status == m.JobStatus.PENDING)).all()
    for job in jobs:
        db_users: Sequence[int] = db.scalars(select(m.User.id).where(m.User.id != job.owner_id)).all()
        users: set[int] = set(random.choices(db_users, k=count))

        for user in users:
            appl: m.Application = m.Application(
                worker_id=user,
                job_id=job.id,
                type=random.choice(types),
            )
        db.add(appl)

    db.commit()
    log(log.INFO, "Created %s applications", count)


def create_applications_for_job(db: Session, job_id: int, count: int = APPLICATIONS_COUNT):
    """Creates application for a job

    Args:
        db (Session): Session to use
        job_id (int): job id to create application for
        count (int, optional): count of application to Defaults to APPLICATIONS_COUNT.
    """
    job_owner_id: int | None = db.scalar(select(m.Job.owner_id).where(m.Job.id == job_id))
    if not job_owner_id:
        log(log.ERROR, "Job [%s] not found", job_id)
        raise ValueError(f"Job [{job_id}] not found")

    db_users: Sequence[int] = db.scalars(select(m.User.id).where(m.User.id != job_owner_id)).all()
    users: set[int] = set(random.choices(db_users, k=count))

    for user in users:
        appl: m.Application = m.Application(
            worker_id=user,
            job_id=job_id,
            type=random.choice(list(m.ApplicationType)),
        )
    db.add(appl)
    db.commit()
    log(log.INFO, "Created application for job [%s]", job_id)
