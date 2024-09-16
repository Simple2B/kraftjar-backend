import random

from faker import Faker
from typing import Sequence

from sqlalchemy.orm import Session
from sqlalchemy import select

from app import models as m
from app.logger import log
from app import schema as s

# from .address import create_addresses

faker: Faker = Faker()


def create_job(db: Session, user_id: int, is_pending=False) -> m.Job:
    """Creates a job for a user

    Args:
        db (Session): Session to use
        user_id (int): User id to create job for
        is_pending (bool, optional): if it's true - creates job with status Pending. Defaults to False.

    Returns:
        m.Job: Created job
    """
    addresses: Sequence[int] = db.scalars(select(m.Address.id)).all()

    if not addresses:
        log(log.ERROR, "No addresses found")
        # create_addresses(db)
        addresses = db.scalars(select(m.Address.id)).all()

    locations: Sequence[int] = db.scalars(select(m.Location.id)).all()

    statuses = [s.JobStatus.PENDING] if is_pending else list(s.JobStatus)
    # random titles, services, locations in ukrainian

    job: m.Job = m.Job(
        title=faker.job(),
        description=faker.text(),
        owner_id=user_id,
        location_id=random.choice(locations),
        status=random.choice(statuses),
    )

    if job.status != s.JobStatus.PENDING:
        job.worker_id = random.choice(db.scalars(select(m.User.id).where(m.User.id != user_id)).all())

    db.add(job)
    db.commit()
    log(log.INFO, "Created job [%s] for user [%s]", job.title, job.owner_id)
    return job


def create_jobs(db: Session, is_pending=False):
    """Creates jobs for all users

    Args:
        db (Session): Session to use
        is_pending (bool, optional): if it's true - creates job with status Pending. Defaults to False.
    """
    users: Sequence[int] = db.scalars(select(m.User.id)).all()
    for user_id in users:
        create_job(db, user_id, is_pending)
