from datetime import datetime
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
import sqlalchemy as sa

from google.oauth2 import id_token
from google.auth.transport import requests

import api.controllers as c
from api.controllers.user import create_out_search_users, get_user_google_account
import app.models as m
import app.schema as s
from api.dependency import get_current_user
from app.database import get_db
from app.logger import log
from app.schema.language import Language
from config import config

CFG = config()

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=s.UserProfileOut,
)
def get_current_user_profile(
    lang: Language = Language.UA,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns the current user profile"""

    log(log.INFO, f"User {current_user.fullname} - {current_user.id} requested his profile")
    return c.get_user_profile(current_user.uuid, lang, db)


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
    lang: Language = Language.UA,
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
    lang: Language = Language.UA,
    db: Session = Depends(get_db),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
):
    """Returns the user profile for public view"""
    return c.get_public_user_profile(user_uuid, lang, db)


@user_router.get("/public-top-experts/", status_code=status.HTTP_200_OK, response_model=s.PublicTopExpertsOut)
def get_public_top_experts(
    lang: Language = Language.UA,
    db: Session = Depends(get_db),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Experts not found"},
    },
):
    """Returns 15 best experts (for carousel)"""

    has_services = m.user_services.c.user_id == m.User.id

    experts = db.scalars(
        sa.select(m.User)
        .where(m.User.is_deleted.is_(False), has_services)
        .order_by(m.User.average_rate.desc())
        .distinct()
        .limit(CFG.USER_CAROUSEL_LIMIT)
    ).all()

    return s.PublicTopExpertsOut(top_experts=create_out_search_users(experts, lang, db))


@user_router.post("/register-google-account", status_code=status.HTTP_201_CREATED)
def register_google_account(
    auth_data: s.GoogleAuthIn,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    responses={
        status.HTTP_409_CONFLICT: {"description": "This Google account is already in use"},
    },
):
    """Register Google account for user"""

    id_info_res: s.GoogleTokenVerification = id_token.verify_oauth2_token(
        auth_data.id_token,
        requests.Request(),
        CFG.GOOGLE_CLIENT_ID,
    )

    email = id_info_res.email
    oauth_id = id_info_res.sub

    google_account = get_user_google_account(email, oauth_id, current_user, db)

    if google_account:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This Google account is already in use")

    new_google_account = m.AuthAccount(
        user_id=current_user.id, email=email, auth_type=s.AuthType.GOOGLE, oauth_id=oauth_id
    )
    db.add(new_google_account)
    db.commit()

    log(log.INFO, "User [%s] successfully added Google account, email: [%s]", current_user.fullname, email)


@user_router.delete("/delete-google-account/{auth_account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_google_account(
    auth_account_id: str,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Google account not found"},
    },
):
    """Delete Google account for user"""

    google_account_filter = sa.and_(
        m.AuthAccount.oauth_id == auth_account_id,
        m.AuthAccount.user_id == current_user.id,
    )

    google_account = db.scalar(sa.select(m.AuthAccount).where(google_account_filter))

    if not google_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Google account not found")

    if google_account.auth_type == s.AuthType.BASIC:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You can't delete basic account")

    current_timestamp = datetime.now()

    google_account.is_deleted = True
    google_account.email = f"deleted-{current_timestamp}"
    google_account.oauth_id = f"deleted-{current_timestamp}"
    db.commit()

    log(
        log.INFO, "User [%s] successfully delete Google account, phone: [%s]", current_user.fullname, current_user.phone
    )
