from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
import sqlalchemy as sa

from google.oauth2 import id_token
from google.auth.transport import requests

import api.controllers as c
from api.controllers.user import create_out_search_users, get_user_auth_account
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


@user_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=s.UsersOut,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Users not found"}},
)
def get_users(
    query: str = Query(default="", max_length=128),
    lang: Language = Language.UA,
    selected_locations: Annotated[list[str] | None, Query()] = None,
    order_by: s.UsersOrderBy = s.UsersOrderBy.AVERAGE_RATE,
    ascending: bool = True,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get users by query params"""

    db_users = sa.select(m.User).where(m.User.is_deleted.is_(False), m.User.id != current_user.id)

    # TODO: All Ukraine select
    if selected_locations or current_user.locations:
        db_users = c.filter_users_by_locations(selected_locations, db, current_user, db_users)

    users = c.filter_and_order_users(query, lang, db, current_user, db_users, order_by)

    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Users not found")

    if not ascending:
        users = users[::-1]

    users_out = create_out_search_users(users, lang, db)

    return s.UsersOut(items=users_out)


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


@user_router.post(
    "/register-google-account",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"description": "This Google account is already in use"},
    },
)
def register_google_account(
    auth_data: s.GoogleAuthIn,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register Google account for user"""

    id_info_res: s.GoogleTokenVerification = id_token.verify_oauth2_token(
        auth_data.id_token,
        requests.Request(),
        CFG.GOOGLE_CLIENT_ID,
    )

    id_info = s.GoogleTokenVerification.model_validate(id_info_res)

    email = id_info.email
    oauth_id = id_info.sub

    google_account = get_user_auth_account(email, oauth_id, db, s.AuthType.GOOGLE)

    if google_account:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This Google account is already in use")

    new_google_account = m.AuthAccount(
        user_id=current_user.id, email=email, auth_type=s.AuthType.GOOGLE, oauth_id=oauth_id
    )
    db.add(new_google_account)
    db.commit()

    log(log.INFO, "User [%s] successfully added Google account, email: [%s]", current_user.fullname, email)


@user_router.post(
    "/register-apple-account",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"description": "This Apple account is already in use"},
    },
)
def register_apple_account(
    auth_data: s.AppleAuthTokenIn,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register Apple account for user"""

    token_data: s.AppleTokenVerification = c.verify_apple_token(auth_data)

    email = token_data.email
    oauth_id = token_data.sub

    apple_account = get_user_auth_account(email, oauth_id, db, s.AuthType.APPLE)

    if apple_account:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This Apple account is already in use")

    new_apple_account = m.AuthAccount(
        user_id=current_user.id, email=email, auth_type=s.AuthType.APPLE, oauth_id=oauth_id
    )
    db.add(new_apple_account)
    db.commit()

    log(log.INFO, "User [%s] successfully added Apple account, email: [%s]", current_user.fullname, email)


@user_router.delete(
    "/auth-account/{auth_account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Auth account not found"},
    },
)
def delete_auth_account(
    auth_account_id: int,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete auth account for user"""

    auth_account_filter = sa.and_(
        m.AuthAccount.id == auth_account_id,
        m.AuthAccount.user_id == current_user.id,
    )

    auth_account = db.scalar(sa.select(m.AuthAccount).where(auth_account_filter))

    if not auth_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auth account not found")

    if auth_account.auth_type == s.AuthType.BASIC:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You can't delete basic account")

    current_timestamp = datetime.now()

    auth_account.is_deleted = True
    auth_account.email = f"deleted-{current_timestamp}"
    auth_account.oauth_id = f"deleted-{current_timestamp}"
    db.commit()

    log(
        log.INFO,
        "User [%s] successfully deleted auth account: [%s], phone: [%s]",
        current_user.fullname,
        auth_account.auth_type,
        current_user.phone,
    )
