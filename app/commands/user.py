import json
from pathlib import Path

import sqlalchemy as sa

from app import models as m
from app import schema as s
from app.database import db
from app.logger import log

MODULE_PATH = Path(__file__).parent
JSON_FILE = MODULE_PATH / ".." / ".." / "data" / "users.json"


def export_users_from_json_file(with_print: bool = True):
    """Fill users with data from json file"""

    with open(JSON_FILE, "r") as file:
        file_data: s.UsersFile = s.UsersFile.model_validate(json.load(file))

    with db.begin() as session:
        if not session.scalar(sa.select(m.Location)):
            log(log.ERROR, "Locations table is empty")
            log(log.ERROR, "Please run `flask export-regions` first")
            raise Exception("Locations table is empty. Please run `flask export-regions` first")

        if not session.scalar(sa.select(m.Service)):
            log(log.ERROR, "Services table is empty")
            log(log.ERROR, "Please run `flask export-services` first")
            raise Exception("Services table is empty. Please run `flask export-services` first")

        for user in file_data.users:
            if session.scalar(sa.select(m.User).where(m.User.phone == user.phone)):
                log(log.INFO, "User with phone [%s] already exists", user.phone)
                continue

            new_user: m.User = m.User(
                fullname=user.fullname,
                phone=user.phone,
                email=user.email,
                password=user.password,
                is_volunteer=user.is_volunteer,
            )

            for location_id in user.location_ids:
                location: m.Location | None = session.scalar(sa.select(m.Location).where(m.Location.id == location_id))
                if not location:
                    log(log.ERROR, "Location with id [%s] not found", location_id)
                    raise Exception(f"Location with id [{location_id}] not found")
                new_user.locations.append(location)

            for service_id in user.service_ids:
                service: m.Service | None = session.scalar(sa.select(m.Service).where(m.Service.id == service_id))
                if not service:
                    log(log.ERROR, "Service with id [%s] not found", service_id)
                    raise Exception(f"Service with id [{service_id}] not found")
                new_user.services.append(service)

            session.add(new_user)
            if with_print:
                log(log.INFO, f"Created user {user.fullname}")
