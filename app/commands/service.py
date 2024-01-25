import json

import sqlalchemy as sa
from sqlalchemy.orm import Session
from app import models as m
from app import schema as s
from app.database import db


JSON_FILE = "data/services.json"


def print_added_services(service: m.Service, session: Session):
    """Print added services"""

    print("+ ", end="")
    stack = [service]
    service = session.scalar(sa.select(m.Service).where(m.Service.id == service.parent_id))
    while service:
        stack.append(service)
        service = session.scalar(sa.select(m.Service).where(m.Service.id == service.parent_id))
    first = True
    for service in reversed(stack):
        if first:
            first = False
            print(service, end="")
        else:
            print(" ->", service, end="")

    print()


def check_if_service_exists(services: dict[int, s.ServiceData], service: s.ServiceData):
    """Check if service exists in db"""
    with db.begin() as session:
        stmt = sa.select(m.Service).where(m.Service.name_ua == service.name_ua)
        db_service = session.scalar(stmt)
        if not db_service:
            return False
        # TODO: check by parent
        return True


def fill_services_from_json_file():
    """Fill services with data from json file"""

    with open(JSON_FILE, "r") as file:
        file_data = s.ServiceDataFile.model_validate(json.load(file))
    services: dict[int, s.ServiceData] = {s.id: s for s in file_data.services}

    with db.begin() as session:
        for service in services.values():
            if check_if_service_exists(services, service):
                continue
            if service.parent_id:
                parent = services[service.parent_id]
                service_db = m.Service(
                    name_ua=service.name_ua,
                    name_en=service.name_en,
                    parent_id=parent.db_id,
                )
            else:
                service_db = m.Service(
                    name_ua=service.name_ua,
                    name_en=service.name_en,
                )
            session.add(service_db)
            session.flush()
            service.db_id = service_db.id
            print_added_services(service_db, session)
