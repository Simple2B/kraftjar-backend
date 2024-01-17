from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import sqlalchemy as sa

import app.models as m
from api.dependency import get_db
from api.oauth2 import create_access_token
from app import schema as s
from app.logger import log
from config import config

router = APIRouter(prefix="/auth", tags=["Auth"])

CFG = config()


@router.post("/login", status_code=status.HTTP_200_OK, response_model=s.Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db=Depends(get_db)):
    """Logs in a user"""
    user = m.User.authenticate(form_data.username, form_data.password, session=db)
    if not user:
        log(log.ERROR, "User [%s] wrong username or password", form_data.username)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
    log(log.INFO, "User [%s] logged in", user.phone)
    return s.Token(access_token=create_access_token(user.id))


@router.post("/token", status_code=status.HTTP_200_OK, response_model=s.Token)
def get_token(auth_data: s.Auth, db=Depends(get_db)):
    """Logs in a user"""
    user = m.User.authenticate(auth_data.identificator, auth_data.password, session=db)
    if not user:
        log(log.ERROR, "User [%s] wrong identificator or password", auth_data.identificator)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
    return s.Token(access_token=create_access_token(user.id))


@router.post("/google", status_code=status.HTTP_200_OK, response_model=s.Token)
def google_auth(
    data: s.GoogleAuth,
    db: Session = Depends(get_db),
):
    """Logs in a user with Google"""

    user = db.scalar(sa.select(m.User).where(m.User.email == data.email))
    if not user:
        first_name = data.first_name if data.first_name else data.display_name

        user = m.User(
            first_name=first_name if first_name else data.email.split("@")[0],
            email=data.email,
            password=CFG.GOOGLE_DEFAULT_PASSWORD,
            phone=data.phone if data.phone else None,
            google_id=data.uid,
        )

        db.add(user)
        db.flush()
        if data.locations:
            for location_id in data.locations:
                location = db.scalar(sa.select(m.Location).where(m.Location.id == location_id))
                if not location:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
                db.add(m.UserLocation(user_id=user.id, location_id=location.id))
        if data.professions:
            for profession_id in data.professions:
                profession = db.scalar(sa.select(m.Profession).where(m.Profession.id == profession_id))
                if not profession:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profession not found")
                db.add(m.UserProfession(user_id=user.id, profession_id=profession.id))

        db.commit()

    return s.Token(access_token=create_access_token(user.id))
