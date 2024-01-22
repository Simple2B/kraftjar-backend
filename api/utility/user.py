import random
from typing import Sequence, cast

from alchemical.flask import Alchemical
from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models as m
from app.logger import log

from .profession import create_professions
from .location import create_locations

faker: Faker = Faker()

USER_COUNT = 10


def create_users(db: Session, count: int = USER_COUNT):
    """Creates users overall

    Args:
        db (Session): Database session
        count (int, optional): Number of users to create. Defaults to USER_COUNT.
    """
    if type(db) != Session:
        db = cast(Alchemical, db).session
    locations: Sequence[int] = db.scalars(select(m.Location.id)).all()
    if not locations:
        log(log.ERROR, "No locations found")
        create_locations(db)
        created_locations: Sequence[int] = db.scalars(select(m.Location.id)).all()
        locations = created_locations

    professions: Sequence[int] = db.scalars(select(m.Profession.id)).all()
    if not professions:
        log(log.ERROR, "No professions found")
        create_professions(db)
        created_professions: Sequence[int] = db.scalars(select(m.Profession.id)).all()
        professions = created_professions

    for i in range(count):
        db.add(
            m.User(
                first_name=faker.first_name(),
                last_name=faker.last_name(),
                email=faker.email(),
                phone=i,
            )
        )
        user_locations = set(random.choices(locations, k=3))
        for location in user_locations:
            db.add(
                m.UserLocation(
                    user_id=i,
                    location_id=location,
                )
            )

        user_professions = set(random.choices(professions, k=3))
        for profession in user_professions:
            db.add(
                m.UserProfession(
                    user_id=i,
                    profession_id=profession,
                )
            )

    db.commit()
    log(log.INFO, "Created %s users", count)
