from typing import Annotated
from fastapi import APIRouter, Depends, Query, UploadFile, status, HTTPException
from mypy_boto3_s3 import S3Client
from sqlalchemy.orm import Session
import sqlalchemy as sa

from google.oauth2 import id_token
from google.auth.transport import requests

import api.controllers as c
from api.controllers.user import create_out_search_users, get_user_auth_account
from api.dependency.s3_client import get_s3_connect
from api.utils import get_file_extension, mark_as_deleted
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


@user_router.get(
    "/{user_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=s.UserProfileOut,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
    dependencies=[Depends(get_current_user)],
)
def get_user_profile(
    user_uuid: str,
    lang: Language = Language.UA,
    db: Session = Depends(get_db),
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

    try:
        id_info_res: s.GoogleTokenVerification = id_token.verify_oauth2_token(
            auth_data.id_token,
            requests.Request(),
            CFG.GOOGLE_CLIENT_ID,
        )

        log(log.INFO, "id_info_res: [%s]", id_info_res)

        id_info = s.GoogleTokenVerification.model_validate(id_info_res)

        email = id_info.email
        oauth_id = id_info.sub

        google_account = get_user_auth_account(email, oauth_id, db, s.AuthType.GOOGLE)

        log(log.INFO, "google_account: [%s]", google_account)

        if google_account:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This Google account is already in use")

        new_google_account = m.AuthAccount(
            user_id=current_user.id, email=email, auth_type=s.AuthType.GOOGLE, oauth_id=oauth_id
        )
        log(log.INFO, "new_google_account: [%s]", new_google_account)
        db.add(new_google_account)
        db.commit()

    except HTTPException as e:
        log(log.ERROR, "Google auth failed: %s", e)
        raise e

    except ValueError as e:
        log(log.ERROR, "Invalid token: %s", e)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")

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


@user_router.put(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=s.UserPut,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
)
def update_user(
    user_data: s.UserPut,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user profile"""

    basic_auth = current_user.basic_auth_account

    if not basic_auth:
        log(log.ERROR, "User [%s] has no basic auth account", current_user.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Basic auth account not found")

    if user_data.services:
        current_user.services.clear()
        for service_uuid in user_data.services:
            service: m.Service | None = db.scalar(sa.select(m.Service).where(m.Service.uuid == service_uuid))
            if not service:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service not found")
            current_user.services.append(service)

    if user_data.locations:
        current_user.locations.clear()
        for location_uuid in user_data.locations:
            location: m.Location | None = db.scalar(sa.select(m.Location).where(m.Location.uuid == location_uuid))
            if not location:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Location not found")
            current_user.locations.append(location)

    if user_data.fullname:
        current_user.fullname = user_data.fullname

    if user_data.description:
        current_user.description = user_data.description

    if user_data.email:
        basic_auth.email = user_data.email

    db.commit()
    log(log.INFO, "User [%s] successfully updated profile", current_user.fullname)

    return s.UserPut(
        fullname=current_user.fullname,
        email=basic_auth.email,
        description=current_user.description,
        locations=[loc.uuid for loc in current_user.locations],
        services=[s.uuid for s in current_user.services],
    )


@user_router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
)
def delete_user(
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete user profile"""

    if not current_user.auth_accounts:
        log(log.ERROR, "User [%s] has no auth accounts, at least basic account should be present", current_user.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auth accounts not found")

    deleted_mark = mark_as_deleted()

    current_user.is_deleted = True
    current_user.phone = deleted_mark
    current_user.fullname = deleted_mark

    for auth_account in current_user.auth_accounts:
        deleted_mark = mark_as_deleted()

        auth_account.is_deleted = True
        auth_account.email = deleted_mark
        auth_account.oauth_id = deleted_mark

    db.commit()
    log(log.INFO, "User [%s] successfully deleted profile", current_user.fullname)


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

    auth_account = next((acc for acc in current_user.auth_accounts if acc.id == auth_account_id), None)

    if not auth_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auth account not found")

    if auth_account.auth_type == s.AuthType.BASIC:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You can't delete basic account")

    deleted_mark = mark_as_deleted()

    auth_account.is_deleted = True
    auth_account.email = deleted_mark
    auth_account.oauth_id = deleted_mark
    db.commit()

    log(
        log.INFO,
        "User [%s] successfully deleted auth account: [%s], phone: [%s]",
        current_user.fullname,
        auth_account.auth_type,
        current_user.phone,
    )


@user_router.put(
    "/favorite-job/{job_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Job not found"},
    },
)
def update_favorite_jobs(
    job_uuid: str,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Add job to the favorite list"""

    job = db.scalar(sa.select(m.Job).where(m.Job.uuid == job_uuid))

    if not job:
        log(log.ERROR, "Job [%s] not found", job_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.owner_id == current_user.id:
        log(log.ERROR, "User [%s] can't add his own job to favorite list", current_user.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User can't add his own job to favorite list")

    if job in current_user.favorite_jobs:
        log(log.INFO, "User [%s] already has job [%s] in favorite list", current_user.id, job_uuid)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job already in favorite list")

    current_user.favorite_jobs.append(job)

    db.commit()
    db.refresh(current_user)
    log(log.INFO, "User [%s] successfully updated favorite job list", current_user.id)


@user_router.delete(
    "/favorite-job/{job_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Job not found"},
    },
)
def delete_favorite_jobs(
    job_uuid: str,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Remove job from favorite list"""

    job = db.scalar(sa.select(m.Job).where(m.Job.uuid == job_uuid))

    if not job:
        log(log.ERROR, "Job [%s] not found", job_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.owner_id == current_user.id:
        log(log.ERROR, "User [%s] can't add his own job to favorite list", current_user.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User can't add his own job to favorite list")

    if job not in current_user.favorite_jobs:
        log(log.INFO, "User [%s] doesn't have job [%s] in favorite list", current_user.id, job_uuid)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job not in favorite list")

    current_user.favorite_jobs.remove(job)

    db.commit()
    db.refresh(current_user)

    log(log.INFO, "User [%s] successfully updated favorite job list", current_user.id)


@user_router.put(
    "/favorite-expert/{expert_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Job not found"},
    },
)
def update_favorite_experts(
    expert_uuid: str,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Add experts to the favorite list"""

    expert = db.scalar(sa.select(m.User).where(m.User.uuid == expert_uuid))

    if not expert:
        log(log.ERROR, "User [%s] not found", expert_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if expert.id == current_user.id:
        log(log.ERROR, "User [%s] can't add himself to favorite list", current_user.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User can't add himself to favorite list")

    if expert in current_user.favorite_experts:
        log(log.INFO, "User [%s] already has expert [%s] in favorite list", current_user.id, expert_uuid)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Expert already in favorite list")

    current_user.favorite_experts.append(expert)

    db.commit()
    db.refresh(current_user)

    log(log.INFO, "User [%s] successfully updated favorite experts list", current_user.id)


@user_router.delete(
    "/favorite-expert/{expert_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Job not found"},
    },
)
def delete_favorite_experts(
    expert_uuid: str,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Remove experts from favorite list"""

    expert = db.scalar(sa.select(m.User).where(m.User.uuid == expert_uuid))

    if not expert:
        log(log.ERROR, "User [%s] not found", expert_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if expert.id == current_user.id:
        log(log.ERROR, "User [%s] can't add himself to favorite list", current_user.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User can't add himself to favorite list")

    if expert not in current_user.favorite_experts:
        log(log.INFO, "User [%s] doesn't have expert [%s] in favorite list", current_user.id, expert_uuid)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Expert not in favorite list")

    current_user.favorite_experts.remove(expert)

    db.commit()
    db.refresh(current_user)

    log(log.INFO, "User [%s] successfully updated favorite experts list", current_user.id)


@user_router.put(
    "/avatar",
    status_code=status.HTTP_200_OK,
    response_model=s.UserPut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Unknown file extension"},
    },
    dependencies=[Depends(get_current_user)],
)
def upload_user_avatar(
    file: UploadFile,
    db: Session = Depends(get_db),
    s3_client: S3Client = Depends(get_s3_connect),
    current_user: m.User = Depends(get_current_user),
):
    """Uploads file for user avatar"""

    extension = get_file_extension(file)

    file_type = c.get_file_type(extension)

    if file_type == s.FileType.UNKNOWN:
        log(log.ERROR, "Unknown file extension [%s]", extension)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown file extension")

    file_model = c.create_file(
        file=file,
        db=db,
        s3_client=s3_client,
        extension=extension,
        file_type=file_type,
        file_name_url=f"users/{current_user.uuid}/avatar",
    )

    current_user.avatar_id = file_model.id
    db.commit()

    log(log.INFO, "User [%s] avatar was added", current_user.id)

    return s.UserPut(
        fullname=current_user.fullname,
        email=current_user.basic_auth_account.email,
        description=current_user.description,
        locations=[loc.uuid for loc in current_user.locations],
        services=[s.uuid for s in current_user.services],
        avatar_url=current_user.avatar.url,
    )
