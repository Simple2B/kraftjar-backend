from typing import Literal

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import api.controllers as c
import app.models as m
import app.schema as s
from api.dependency import get_current_user
from app.database import get_db
from app.logger import log
from config import config

CFG = config()

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.get("/me", status_code=status.HTTP_200_OK, response_model=s.User)
def get_current_user_profile(
    current_user: m.User = Depends(get_current_user),
):
    """Returns the current user profile"""

    log(log.INFO, f"User {current_user.fullname} - {current_user.id} requested his profile")
    return current_user


@user_router.post("/search", status_code=status.HTTP_200_OK, response_model=s.UsersSearchOut)
def search_users(
    query: s.UserSearchIn,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    responses={
        status.HTTP_409_CONFLICT: {"description": "Selected service not found"},
    },
):
    """Returns filtered list of users"""
    return c.search_users(query, current_user, db)


@user_router.get("/{user_uuid}", status_code=status.HTTP_200_OK, response_model=s.UserProfileOut)
def get_user_profile(
    user_uuid: str,
    lang: Literal[CFG.UA, CFG.EN] = CFG.UA,  # type: ignore
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
):
    """Returns the user profile"""
    return c.get_user_profile(user_uuid, lang, db)


@user_router.post("/search-public", status_code=status.HTTP_200_OK, response_model=s.PublicUsersSearchOut)
def public_search_users(
    query: s.UserSearchIn,
    db: Session = Depends(get_db),
    responses={
        status.HTTP_409_CONFLICT: {"description": "Selected service not found"},
    },
):
    """Returns filtered list of users"""

    result = c.public_search_users(query, db)
    return result


@user_router.get("/public/{user_uuid}", status_code=status.HTTP_200_OK, response_model=s.PublicUserProfileOut)
def get_public_user_profile(
    user_uuid: str,
    lang: Literal[CFG.UA, CFG.EN] = CFG.UA,  # type: ignore
    db: Session = Depends(get_db),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
):
    """Returns the user profile for public view"""
    return c.get_public_user_profile(user_uuid, lang, db)
