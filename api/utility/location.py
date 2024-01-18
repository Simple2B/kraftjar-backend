from typing import Sequence

from faker import Faker
from sqlalchemy.orm import Session

from app import models as m
from app.logger import log

faker: Faker = Faker()

LOCATIONS_COUNT = 10


def create_locations(db: Session, count: int = LOCATIONS_COUNT):
    """Creates locations overall

    Args:
        db (Session): Database session
        count (int, optional): Number of locations to create. Defaults to LOCATIONS_COUNT.w
    """
    locations: Sequence[m.Location] = [m.Location(name=faker.city()) for _ in range(count)]
    db.add_all(locations)
    db.commit()
    log(log.INFO, "Created %s locations", count)
