import random

from faker import Faker
from typing import Sequence

from sqlalchemy.orm import Session
from sqlalchemy import select

from app import models as m
from app.logger import log

from .address import create_addresses
from .service import create_services

faker: Faker = Faker()


def create_job(db: Session, user_id: int):
    """Create a job for a user"""
    addresses: Sequence[int] = db.scalars(select(m.Address.id)).all()

    if not addresses:
        log(log.ERROR, "No addresses found")
        create_addresses(db)
        new_addresses: Sequence[int] = db.scalars(select(m.Address.id)).all()
        addresses = new_addresses

    services: Sequence[int] = db.scalars(select(m.Service.id)).all()
    if not services:
        log(log.ERROR, "No services found")
        create_services(db)
        new_services: Sequence[int] = db.scalars(select(m.Service.id)).all()
        services = new_services

    locations: Sequence[int] = db.scalars(select(m.Location.id)).all()

    job: m.Job = m.Job(
        title=faker.job(),
        description=faker.text(),
        owner_id=user_id,
        address_id=random.choice(addresses),
        time=faker.time(),
        location_id=random.choice(locations),
        status=random.choice(list(m.JobStatus)),
    )

    if job.status != m.JobStatus.PENDING:
        job.worker_id = random.choice(db.scalars(select(m.User.id).where(m.User.id != user_id)).all())

    db.add(job)
    db.commit()
    log(log.INFO, "Created job [%s] for user [%s]", job.title, job.owner_id)
    return job


def create_jobs(db: Session):
    """Create jobs for all users"""
    users: Sequence[int] = db.scalars(select(m.User.id)).all()
    for user_id in users:
        create_job(db, user_id)
