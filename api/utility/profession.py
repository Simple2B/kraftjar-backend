from typing import Sequence

from faker import Faker
from sqlalchemy.orm import Session

from app import models as m
from app.logger import log

faker: Faker = Faker()

PROFESSIONS_COUNT = 10


def create_professions(db: Session, count: int = PROFESSIONS_COUNT):
    """Creates professions overall

    Args:
        db (Session): Database session
    """
    professions: Sequence[m.Profession] = [m.Profession(name=faker.word()) for _ in range(count)]
    db.add_all(professions)
    db.commit()
    log(log.INFO, "Created %s professions", count)
