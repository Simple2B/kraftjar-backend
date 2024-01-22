from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import app.models as m
from api.dependency import get_db
from api.oauth2 import create_access_token
from app import schema as s
from api import controllers as c
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
    user = m.User.authenticate(auth_data.phone, auth_data.password, session=db)
    if not user:
        log(log.ERROR, "User [%s] wrong phone or password", auth_data.phone)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
    return s.Token(access_token=create_access_token(user.id))


@router.post("/google", status_code=status.HTTP_200_OK, response_model=s.Token)
def google_auth(
    data: s.GoogleAuth,
    db: Session = Depends(get_db),
):
    """Logs in a user with Google"""

    return c.google_auth(data, db)


@router.post("/apple", status_code=status.HTTP_200_OK, response_model=s.Token)
def apple_auth(
    data: s.AppleAuth,
    db: Session = Depends(get_db),
):
    """Logs in a user with Apple"""

    return c.apple_auth(data, db)
