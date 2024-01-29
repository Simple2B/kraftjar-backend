import sqlalchemy as sa
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import Executable

from app import models as m
from app import schema as s

from .oauth2 import create_access_token


def register_user(user_data: s.RegistrationIn, db: Session) -> s.Token:
    # check if phone is already registered
    stmt: Executable = sa.select(m.User).where(m.User.phone == user_data.phone)
    if db.scalar(stmt) is not None:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="This phone is already registered")

    # check if email is already registered
    stmt = sa.select(m.User).where(m.User.email == user_data.email)
    if db.scalar(stmt) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This email is already registered")

    user: m.User = m.User(
        fullname=user_data.fullname,
        phone=user_data.phone,
        email=user_data.email,
        password=user_data.password,
        is_volunteer=user_data.is_volunteer,
    )
    db.add(user)
    # link user to services
    for service_uuid in user_data.services:
        service: m.Service | None = db.scalar(sa.select(m.Service).where(m.Service.uuid == service_uuid))
        if not service:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service not found")
        user.services.append(service)

    # link user to locations
    for location_uuid in user_data.locations:
        location: m.Location | None = db.scalar(sa.select(m.Location).where(m.Location.uuid == location_uuid))
        if not location:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Location not found")
        user.locations.append(location)
    db.commit()
    db.refresh(user)
    return s.Token(access_token=create_access_token(user.id))
