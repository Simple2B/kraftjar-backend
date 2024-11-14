from typing import Sequence, Tuple

import sqlalchemy as sa
from fastapi import HTTPException, status
from sqlalchemy.engine.result import Result
from sqlalchemy.orm import Session, aliased

import app.models as m
from app.models.location import Location
import app.schema as s
from app.schema.language import Language
from app.utilities import pop_keys
from config import config

CFG = config()
service_alias = aliased(m.Service)


def create_out_search_users(
    db_users: Sequence[m.User], lang: Language, db: Session, me: m.User | None = None
) -> list[s.UserSearchOut]:
    """Creates list of UserSearchOut from db users"""

    users: list[s.UserSearchOut] = []

    for db_user in db_users:
        services = [
            s.Service(uuid=service.uuid, name=service.name_ua if lang == Language.UA else service.name_en)
            for service in db_user.services
        ]
        regions: Result[Tuple[str, str]] = db.execute(
            sa.select(m.Region.name_ua if lang == Language.UA else m.Region.name_en, m.Location.uuid)
            .join(m.Location)
            .join(m.user_locations)
            .where(m.user_locations.c.user_id == db_user.id)
        )
        locations: list[s.LocationStrings] = [s.LocationStrings(name=name, uuid=uuid) for name, uuid in regions]
        users.append(
            s.UserSearchOut(
                **pop_keys(db_user.__dict__, ["services", "locations"]),
                services=services,
                locations=locations,
                owned_rates_count=db_user.owned_rates_count,
                is_favorite=db_user in me.favorite_experts if me else False,
                avatar_url=db_user.avatar_url,
                receiver_average_rate=db_user.receiver_average_rate,
                lang=lang,
            )
        )
    return users


def get_user_profile(user_uuid: str, lang: Language, db: Session) -> s.UserProfileOut:
    """Returns user profile"""

    db_user: m.User | None = db.scalar(sa.select(m.User).where(m.User.uuid == user_uuid))

    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    services = [
        s.Service(uuid=service.uuid, name=service.name_ua if lang == Language.UA else service.name_en)
        for service in db_user.services
    ]
    regions: Result[Tuple[str, str]] = db.execute(
        sa.select(m.Region.name_ua if lang == Language.UA else m.Region.name_en, m.Location.uuid)
        .join(m.Location)
        .join(m.user_locations)
        .where(m.user_locations.c.user_id == db_user.id)
    )
    locations: list[s.LocationStrings] = [s.LocationStrings(name=name, uuid=uuid) for name, uuid in regions]

    auth_accounts: list[s.AuthAccountOut] = [
        s.AuthAccountOut(
            id=auth_account.id,
            email=auth_account.email,
            auth_type=s.AuthType(auth_account.auth_type),
        )
        for auth_account in db_user.auth_accounts
        if not auth_account.is_deleted
    ]

    completed_jobs_count = db.scalar(
        sa.select(sa.func.count(m.Job.id)).where(
            sa.and_(
                m.Job.is_deleted.is_(False),
                m.Job.worker_id == db_user.id,
                m.Job.status == s.JobStatus.PAYMENT_CONFIRMED.value,
            )
        )
    )

    announced_jobs_count = db.scalar(
        sa.select(sa.func.count(m.Job.id)).where(
            sa.and_(
                m.Job.is_deleted.is_(False),
                m.Job.owner_id == db_user.id,
                m.Job.status == s.JobStatus.PENDING.value,
            )
        )
    )

    private_jobs_count = db.scalar(
        sa.select(sa.func.count(m.Job.id)).where(
            sa.and_(
                m.Job.is_deleted.is_(False),
                m.Job.owner_id == db_user.id,
                m.Job.is_public.is_(False),
                m.Job.status == s.JobStatus.PENDING.value,
            )
        )
    )

    ALL_UKRAINE = "Вся Україна" if lang == Language.UA else "All Ukraine"

    favorite_jobs: list[s.UserFavoriteJob] = []

    for job in db_user.favorite_jobs:
        location = ALL_UKRAINE

        if job.location:
            location = job.location.region[0].name_ua if lang == Language.UA else job.location.region[0].name_en

        address = None
        if job.address:
            lang_name = job.address.line1 if lang == Language.UA else job.address.line2
            lang_type = job.address.street_type_ua if lang == Language.UA else job.address.street_type_en
            address = f"{lang_type} {lang_name}"

        job_owner: m.User | None = db.scalar(sa.select(m.User).where(m.User.id == job.owner_id))

        if not job_owner:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job owner not found")

        job_owner_fullname = f"{job_owner.first_name} {job_owner.last_name[0] if job_owner.last_name else ''}"

        favorite_jobs.append(
            s.UserFavoriteJob(
                job_uuid=job.uuid,
                title=job.title,
                location=location,
                address=address,
                cost=job.cost,
                start_date=job.start_date,
                is_volunteer=job.is_volunteer,
                is_negotiable=job.is_negotiable,
                owner=s.UserShortInfo(
                    uuid=job_owner.uuid,
                    fullname=job_owner_fullname,
                    avatar_url=job_owner.avatar_url,
                ),
            )
        )

    favorite_expert: list[s.UserFavoriteExpert] = []

    for expert in db_user.favorite_experts:
        expert_locations = []

        if expert.locations:
            for loc in expert.locations:
                expert_locations.append(loc.region[0].name_ua if lang == Language.UA else loc.region[0].name_en)

        favorite_expert.append(
            s.UserFavoriteExpert(
                uuid=expert.uuid,
                fullname=expert.fullname,
                locations=expert_locations if expert_locations else [ALL_UKRAINE],
                avatar_url=expert.avatar_url,
            )
        )

    recent_showcases = []
    if db_user.jobs:
        JOBS_LIMIT = 3
        completed_jobs = [job for job in db_user.jobs if job.status == s.JobStatus.PAYMENT_CONFIRMED.value][:JOBS_LIMIT]

        if completed_jobs:
            completed_jobs = sorted(completed_jobs, key=lambda job: job.updated_at, reverse=True)

            for job in completed_jobs:
                recent_showcases.append(
                    s.UserRecentShowcase(
                        title=job.title,
                        description=job.description,
                        rates=[
                            s.RateUserOut(
                                uuid=rate.uuid,
                                receiver_uuid=rate.receiver.uuid,
                                rate=rate.rate,
                                review=rate.review,
                                created_at=rate.created_at,
                                gives=s.UserRateOut(
                                    uuid=rate.giver.uuid,
                                    fullname=rate.giver.fullname,
                                ),
                                avatar_url=rate.giver.avatar_url,
                            )
                            for rate in job.rates
                            if rate.receiver_id == db_user.id
                        ],
                    )
                )

    return s.UserProfileOut(
        # TODO: remove  user.__dict__ add like property in User model and use s.UserProfileOut.model_validate
        **pop_keys(db_user.__dict__, ["favorite_jobs", "favorite_experts", "services", "locations", "auth_accounts"]),
        auth_accounts=auth_accounts,
        services=services,
        locations=locations,
        owned_rates_count=db_user.owned_rates_count,
        avatar_url=db_user.avatar_url,
        completed_jobs_count=completed_jobs_count if completed_jobs_count else 0,
        announced_jobs_count=announced_jobs_count if announced_jobs_count else 0,
        private_jobs_count=private_jobs_count if private_jobs_count else 0,
        favorite_jobs=favorite_jobs,
        favorite_experts=favorite_expert,
        notification_settings=db_user.notification_settings,
        receiver_average_rate=db_user.receiver_average_rate,
        recent_showcases=recent_showcases,
    )


def get_user_auth_account(email: str, oauth_id: str, db: Session, auth_type: s.AuthType) -> m.AuthAccount | None:
    auth_account_filter = sa.and_(
        m.AuthAccount.email == email,
        m.AuthAccount.oauth_id == oauth_id,
        m.AuthAccount.auth_type == auth_type,
    )

    auth_account = db.scalar(sa.select(m.AuthAccount).where(auth_account_filter))
    return auth_account


def filter_users_by_locations(
    selected_locations: list[str] | None,
    db: Session,
    user_locations: list[Location],
    db_users: sa.Select[Tuple[m.User]],
):
    if selected_locations:
        if CFG.ALL_UKRAINE in selected_locations:
            return db_users

        locations = db.execute(sa.select(m.Location).where(m.Location.uuid.in_(selected_locations))).scalars().all()
        db_users = db_users.where(m.User.locations.any(m.Location.uuid.in_([loc.uuid for loc in locations])))
    else:
        db_users = db_users.where(m.User.locations.any(m.Location.uuid.in_([loc.uuid for loc in user_locations])))

    return db_users


def filter_and_order_users(
    query: str,
    lang: Language,
    db: Session,
    user_locations: list[Location] | None,
    db_users: sa.Select[Tuple[m.User]],
    order_by: s.UsersOrderBy,
):
    """Filters and orders users by query params"""

    query = query.strip()

    if query:
        if lang == Language.UA:
            name_lang_query = m.Service.name_ua.ilike(f"%{query}%")
        else:
            name_lang_query = m.Service.name_en.ilike(f"%{query}%")

        services = db.execute(sa.select(m.Service).where(name_lang_query)).scalars().all()
        if services:
            db_users = db_users.where(m.User.services.any(m.Service.id.in_([s.id for s in services])))
        else:
            db_users = db_users.where(m.User.fullname.ilike(f"%{query}%"))

    all_users = db.execute(db_users).scalars().all()

    if order_by == s.UsersOrderBy.AVERAGE_RATE:
        users = all_users
        users = sorted(users, key=lambda user: user.receiver_average_rate, reverse=True)
    elif order_by == s.UsersOrderBy.OWNED_RATES_COUNT:
        users = all_users
        users = sorted(users, key=lambda user: user.owned_rates_count, reverse=True)
    elif user_locations and order_by == s.UsersOrderBy.NEAR:
        users = (
            db.execute(
                db_users.order_by(m.User.locations.any(m.Location.id.in_([loc.id for loc in user_locations])).desc())
            )
            .scalars()
            .all()
        )
    else:
        users = all_users

    return users
