import sqlalchemy as sa
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app import schema as s
from app import models as m
from .oauth2 import create_access_token


def register_user(user_data: s.RegistrationIn, db: Session) -> s.Token:
    # check if phone is already registered
    stmt = sa.select(m.User).where(m.User.phone == user_data.phone)
    if db.scalar(stmt) is not None:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="This phone is already registered")

    # check if email is already registered
    stmt = sa.select(m.User).where(m.User.email == user_data.email)
    if db.scalar(stmt) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This email is already registered")

    user = m.User(
        fullname=user_data.fullname,
        phone=user_data.phone,
        email=user_data.email,
        password=user_data.password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return s.Token(access_token=create_access_token(user.id))
