import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import sqlalchemy as sa
from google.oauth2 import id_token
from google.auth.transport import requests

import app.models as m
from api.dependency import get_db, get_current_user
from api.controllers.oauth2 import create_access_token
from app import schema as s
from api import controllers as c
from app.logger import log
from config import config

ISSUER_WHITELIST = ["accounts.google.com", "https://accounts.google.com"]

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
    user = m.User.authenticate(auth_data.phone, auth_data.password, session=db)
    if not user:
        log(log.ERROR, "User [%s] wrong phone or password", auth_data.phone)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
    return s.Token(access_token=create_access_token(user.id))


@router.post("/google", status_code=status.HTTP_200_OK, response_model=s.Token)
def google_auth(auth_data: s.GoogleAuthIn, db: Session = Depends(get_db)):
    """Validates google auth token and returns a JWT token"""
    log(log.INFO, "Validating google token")

    try:
        id_info_res = id_token.verify_oauth2_token(
            auth_data.id_token,
            requests.Request(),
            CFG.GOOGLE_CLIENT_ID,
        )

        id_info = s.GoogleTokenVerification.model_validate(id_info_res)

        if id_info.iss not in ISSUER_WHITELIST:
            raise ValueError("Wrong issuer.")

        user = db.scalar(sa.select(m.User).where(sa.and_(m.User.email == id_info.email)))

        if not user:
            log(log.INFO, "[Google Auth] User [%s] not found. Creating a guest user", id_info.email)

            user = m.User(
                email=id_info.email,
                fullname=id_info.name if id_info.name else "",
                first_name=id_info.given_name if id_info.given_name else "",
                last_name=id_info.family_name if id_info.family_name else "",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return s.Token(access_token=create_access_token(user.id))

    except HTTPException as e:
        raise e

    except ValueError as e:
        log(log.ERROR, "Invalid token: %s", e)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")


# save phone for user and send sms with code
@router.post(
    "/phone",
    status_code=status.HTTP_200_OK,
    response_model=s.Token,
    responses={status.HTTP_409_CONFLICT: {"description": "Phone is already in use"}},
)
def save_phone(
    data: s.PhoneAuthIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Saves phone for a user and sends an SMS with a code"""

    # check if phone is already in use
    if db.scalar(sa.select(m.User).where(m.User.phone == data.phone)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone is already in use")

    current_user.phone = data.phone

    # TODO: send sms with code to the phone. Creating a code and save it to the database, add field verification code to the user model

    db.commit()
    db.refresh(current_user)

    return s.Token(access_token=create_access_token(current_user.id))


@router.post("/apple", status_code=status.HTTP_200_OK, response_model=s.Token)
def apple_auth(
    data: s.AppleAuth,
    db: Session = Depends(get_db),
):
    """Logs in a user with Apple"""

    return c.apple_auth(data, db)
