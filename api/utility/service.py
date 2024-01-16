import random
from typing import Sequence

from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models as m
from app.logger import log

from .profession import create_professions

faker: Faker = Faker()

SERVICES_COUNT = 10


def create_services(db: Session, count: int = SERVICES_COUNT):
    """Creates services overall

    Args:
        db (Session): Database session
    """
    professions: Sequence[int] = db.scalars(select(m.Profession.id)).all()

    if not professions:
        log(log.ERROR, "No professions found")
        create_professions(db)
        created_professions: Sequence[int] = db.scalars(select(m.Profession.id)).all()
        professions = created_professions

    services: Sequence[m.Service] = [
        m.Service(
            name=faker.word(),
            profession_id=random.choice(professions),
        )
        for _ in range(count)
    ]
    db.add_all(services)
    db.commit()
    log(log.INFO, "Created %s services", count)
