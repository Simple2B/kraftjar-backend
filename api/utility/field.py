import json

from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models as m
from app import schema as s
from app.logger import log

from .service import create_service

faker: Faker = Faker()

FIELDS = json.load(open("api/utility/fields.json", "r"))


def create_fields(db: Session, with_services: bool = True):
    """Creates fields overall

    Args:
        db (Session): Database session
        with_services (bool, optional): If it's true - creates services too. Defaults to False.
    """
    fields = [s.FieldCreate.model_validate(f) for f in FIELDS]
    for field in fields:
        if db.scalars(select(m.Field.id).where(m.Field.name_ua == field.name_ua)).first():
            log(log.INFO, "Field [%s] already exists", field.name_ua)
            continue
        db.add(m.Field(name_ua=field.name_ua, name_en=field.name_en))
        db.commit()
        if with_services:
            create_field_services(db, field)
        log(log.INFO, "Created field [%s]", field.name_ua)
    log(log.INFO, "Created %s fields", len(fields))


def create_field(db: Session, name_ua: str, name_en: str) -> m.Field:
    """Creates field

    Args:
        db (Session): Database session
        name_ua (str): Ukrainian name of field
        name_en (str): English name of field

    Returns:
        m.Field: Created field
    """
    field: m.Field = m.Field(name_ua=name_ua, name_en=name_en)
    db.add(field)
    db.commit()
    log(log.INFO, "Created field [%s]", name_ua)
    return field


def create_field_services(db: Session, field: s.FieldCreate):
    """Creates connection between services and fields

    Args:
        db (Session): Database session
        field (s.FieldCreate): Field to create services for
    """
    for service in field.services:
        service_id: int | None = db.scalars(select(m.Service.id).where(m.Service.name_ua == service)).first()
        if not service_id:
            service_id = create_service(db, service).id
        field_id: int | None = db.scalars(select(m.Field.id).where(m.Field.name_ua == field.name_ua)).first()
        if not field_id:
            create_field(db, field.name_ua, field.name_en)
        db.add(m.FieldService(service_id=service_id, field_id=field_id))
        db.commit()
    log(log.INFO, "Created services for field [%s]", field.name_ua)
