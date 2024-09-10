from typing import cast

from alchemical.flask import Alchemical
from faker import Faker
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.schema.auth import AuthType

from app import models as m
from app.logger import log

faker: Faker = Faker()

USER_COUNT = 10


def create_locations():
    from app.commands.locations import export_regions_from_json_file

    export_regions_from_json_file(with_print=False)


def create_users(db: Session, count: int = USER_COUNT):
    """Creates users overall

    Args:
        db (Session): Database session
        count (int, optional): Number of users to create. Defaults to USER_COUNT.
    """
    if type(db) != Session:
        db = cast(Alchemical, db).session
    locations = db.scalars(sa.select(m.Location)).all()
    if not locations:
        log(log.WARNING, "No locations found")
        create_locations()
        locations = db.scalars(sa.select(m.Location)).all()

    for i in range(1, count + 1):
        user = m.User(
            fullname=faker.last_name(),
            auth_accounts=[m.AuthAccount(email=faker.email(), auth_type=AuthType.BASIC)],
            phone=faker.phone_number(),
        )
        db.add(user)
        db.flush()

    db.commit()
    log(log.INFO, "Created %s users", count)
