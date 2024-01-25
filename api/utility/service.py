from typing import Sequence

from faker import Faker
from sqlalchemy.orm import Session

from app import models as m
from app.logger import log


faker: Faker = Faker()

SERVICES_COUNT = 10


def create_services(db: Session, count: int = SERVICES_COUNT):
    """Creates services overall

    Args:
        db (Session): Database session
        count (int, optional): Number of services to create. Defaults to SERVICES_COUNT.
    """
    services: Sequence[m.Service] = [
        m.Service(
            name_ua=faker.word(),
            name_en=faker.word(),
        )
        for _ in range(count)
    ]
    db.add_all(services)
    db.commit()
    log(log.INFO, "Created %s services", count)


def create_service(db: Session, name_ua: str = "", name_en: str = "") -> m.Service:
    """Creates service for

    Args:
        db (Session): Database session
        name_ua (str, optional): Name of service in ukrainian. Defaults to "".
        name_en (str, optional): Name of service in english. Defaults to "".
    Returns:
        m.Service: Created service
    """
    if not name_ua:
        name_ua = faker.word()
    if not name_en:
        name_en = faker.word()

    service: m.Service = m.Service(
        name_ua=name_ua,
        name_en=name_en,
    )

    db.add(service)
    db.commit()
    log(log.INFO, "Created service [%s]", service.name_en)
    return service
