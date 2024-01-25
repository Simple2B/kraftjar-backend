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
        count (int, optional): Number of services to create. Defaults to SERVICES_COUNT.
    """
    professions: Sequence[int] = db.scalars(select(m.Profession.id)).all()

    if not professions:
        log(log.ERROR, "No professions found")
        create_professions(db)
        professions = db.scalars(select(m.Profession.id)).all()

    services: Sequence[m.Service] = [
        m.Service(
            name_ua=faker.word(),
            name_en=faker.word(),
            profession_id=random.choice(professions),
        )
        for _ in range(count)
    ]
    db.add_all(services)
    db.commit()
    log(log.INFO, "Created %s services", count)


def create_service(db: Session, name_ua: str = "", name_en: str = "", profession_id: int | None = None) -> m.Service:
    """Creates service for a profession

    Args:
        db (Session): Database session
        name_ua (str, optional): Name of service in ukrainian. Defaults to "".
        name_en (str, optional): Name of service in english. Defaults to "".
        profession_id (int, optional): Profession id to create service for. Defaults to None.
    Returns:
        m.Service: Created service
    """
    if not name_ua:
        name_ua = faker.word()
    if not name_en:
        name_en = faker.word()
    if not profession_id:
        professions: Sequence[int] = db.scalars(select(m.Profession.id)).all()
        if not professions:
            log(log.ERROR, "No professions found")
            create_professions(db)
            professions = db.scalars(select(m.Profession.id)).all()
        profession_id = random.choice(professions)

    if not db.scalar(select(m.Profession.id).where(m.Profession.id == profession_id)):
        log(log.ERROR, "No profession found by id: [%s]", profession_id)
        raise ValueError(f"No profession found by id: [{profession_id}]")

    service: m.Service = m.Service(
        name_ua=name_ua,
        name_en=name_en,
        profession_id=profession_id,
    )

    db.add(service)
    db.commit()
    log(log.INFO, "Created service [%s]", service.name_en)
    return service
