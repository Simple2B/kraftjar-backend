from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import api.controllers as c
import app.models as m
import app.schema as s
from api.dependency import get_current_user
from app.database import get_db
from app.logger import log

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.get("/me", status_code=status.HTTP_200_OK, response_model=s.User)
def get_current_user_profile(
    current_user: m.User = Depends(get_current_user),
):
    """Returns the current user profile"""

    log(log.INFO, f"User {current_user.first_name} - {current_user.id} requested his profile")
    return current_user


@user_router.post("/", status_code=status.HTTP_200_OK, response_model=s.UserSearchOut)
def get_users(
    filters: s.UserFilters,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns filtered list of users"""
    return c.get_users(filters, db)
