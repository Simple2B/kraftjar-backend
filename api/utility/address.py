import random
from typing import Sequence

from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models as m
from app.logger import log

from .location import create_locations

faker: Faker = Faker()

ADDRESSES_COUNT = 10


def create_addresses(db: Session, count: int = ADDRESSES_COUNT):
    """Creates addresses overall

    Args:
        db (Session): Database session
    """
    locations: Sequence[int] = db.scalars(select(m.Location.id)).all()

    if not locations:
        log(log.ERROR, "No locations found")
        create_locations(db)
        locations = db.scalars(select(m.Location.id)).all()

    addresses: Sequence[m.Address] = [
        m.Address(
            line1=faker.street_address(),
            line2=faker.secondary_address(),
            city=faker.city(),
            postcode=faker.postcode(),
            location_id=random.choice(locations),
        )
        for _ in range(count)
    ]
    db.add_all(addresses)
    db.commit()
    log(log.INFO, "Created %s addresses", count)
