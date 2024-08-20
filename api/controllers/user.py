import re
from typing import Literal, Sequence, Tuple

import sqlalchemy as sa
from fastapi import HTTPException, status
from sqlalchemy.engine.result import Result
from sqlalchemy.orm import Session, aliased

import app.models as m
import app.schema as s
from app.utilities import pop_keys
from config import config

CFG = config()
service_alias = aliased(m.Service)


def create_out_search_users(db_users: Sequence[m.User], lang: str, db: Session) -> list[s.UserSearchOut]:
    """Creates list of UserSearchOut from db users"""

    users: list[s.UserSearchOut] = []

    for db_user in db_users:
        services = [
            s.Service(uuid=service.uuid, name=service.name_ua if lang == CFG.UA else service.name_en)
            for service in db_user.services
        ]
        regions: Result[Tuple[str, str]] = db.execute(
            sa.select(m.Region.name_ua if lang == CFG.UA else m.Region.name_en, m.Location.uuid)
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
            )
        )
    return users


def search_users(query: s.UserSearchIn, me: m.User, db: Session) -> s.UsersSearchOut:
    """filters users"""

    user_locations: set[s.Location] = {
        s.Location(
            uuid=location.uuid, name=location.region[0].name_en if query.lang == CFG.EN else location.region[0].name_ua
        )
        for location in me.locations
    }

    stmt = (
        sa.select(sa.case({query.lang == CFG.UA: m.Region.name_ua}, else_=m.Region.name_en), m.Location.uuid)
        .select_from(m.Location)
        .join(m.Region)
        .where(
            sa.and_(
                m.Location.uuid.notin_([location.uuid for location in me.locations]),
                sa.not_(
                    m.Location.id.in_(
                        sa.select(m.user_locations.c.location_id).where(m.user_locations.c.user_id == me.id)
                    )
                ),
            )
        )
    )

    db_locations: set[s.Location] = {
        s.Location(uuid=uuid, name=name) for name, uuid in db.execute(stmt, {"id_1": me.id})
    }

    stmt = (
        sa.select(
            m.User,
        )
        .where(m.User.is_deleted.is_(False))
        .distinct()
        .limit(CFG.MAX_USER_SEARCH_RESULTS)
    )
    stmt = stmt.join(m.user_services).join(m.Service)
    if query.query:
        wordList = re.sub(CFG.RE_WORD, " ", query.query).split()
        for word in wordList:
            if len(word) >= 3:
                service_lang_column = m.Service.name_ua if query.lang == CFG.UA else m.Service.name_en
                svc_stmt = sa.select(m.Service).where(service_lang_column.ilike(f"%{word}%"))
                if db.execute(svc_stmt).first():
                    stmt = stmt.where(service_lang_column.ilike(f"%{word}%"))
                else:
                    stmt = stmt.where(m.User.fullname.ilike(f"%{word}%"))
    else:
        db_main_services = db.scalars(sa.select(m.Service).where(m.Service.parent_id.is_(None))).all()
        services = {
            s.Service(uuid=service.uuid, name=service.name_ua if query.lang == CFG.UA else service.name_en)
            for service in db_main_services
        }
        stmt = stmt.where(m.Service.uuid.in_([service.uuid for service in services]))

    stmt = stmt.join(m.user_locations).join(m.Location)
    if CFG.ALL_UKRAINE in query.selected_locations:
        near_users: Sequence[m.User] = db.scalars(
            stmt.where(m.Location.uuid.in_([location.uuid for location in user_locations]))
        ).all()
    else:
        if query.selected_locations:
            stmt = stmt.where(m.Location.uuid.in_(query.selected_locations))
            near_users = []
        else:
            stmt = stmt.where(m.Location.uuid.in_([location.uuid for location in user_locations]))
            near_users = db.scalars(stmt).all()

    top_users: Sequence[m.User] = db.scalars(stmt.order_by(m.User.average_rate.desc())).all()

    return s.UsersSearchOut(
        lang=query.lang,
        locations=[_ for _ in db_locations],
        user_locations=[_ for _ in user_locations],
        selected_locations=query.selected_locations,
        top_users=create_out_search_users(top_users, query.lang, db),
        near_users=create_out_search_users(near_users, query.lang, db),
        query=query.query,
    )


def get_user_profile(user_uuid: str, lang: Literal[CFG.UA, CFG.EN], db: Session) -> s.UserProfileOut:  # type: ignore
    """Returns user profile"""

    db_user: m.User | None = db.scalar(sa.select(m.User).where(m.User.uuid == user_uuid))
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    services = [
        s.Service(uuid=service.uuid, name=service.name_ua if lang == CFG.UA else service.name_en)
        for service in db_user.services
    ]
    regions: Result[Tuple[str, str]] = db.execute(
        sa.select(m.Region.name_ua if lang == CFG.UA else m.Region.name_en, m.Location.uuid)
        .join(m.Location)
        .join(m.user_locations)
        .where(m.user_locations.c.user_id == db_user.id)
    )
    locations: list[s.LocationStrings] = [s.LocationStrings(name=name, uuid=uuid) for name, uuid in regions]

    return s.UserProfileOut(
        **pop_keys(db_user.__dict__, ["services", "locations"]),
        services=services,
        locations=locations,
        owned_rates_count=db_user.owned_rates_count,
    )


def public_search_users(query: s.UserSearchIn, db: Session) -> s.PublicUsersSearchOut:
    """filters users"""

    locations = db.scalars(sa.select(m.Location)).all()

    stmt = (
        sa.select(sa.case({query.lang == CFG.UA: m.Region.name_ua}, else_=m.Region.name_en), m.Location.uuid)
        .select_from(m.Location)
        .join(m.Region)
        .where(
            sa.and_(
                m.Location.uuid.notin_([location.uuid for location in locations]),
            )
        )
    )

    db_locations: set[s.Location] = {s.Location(uuid=uuid, name=name) for name, uuid in db.execute(stmt)}

    stmt = (
        sa.select(
            m.User,
        )
        .where(m.User.is_deleted.is_(False))
        .distinct()
    )
    stmt = stmt.join(m.user_services).join(m.Service)
    if query.query:
        wordList = re.sub(CFG.RE_WORD, " ", query.query).split()
        for word in wordList:
            if len(word) >= 3:
                service_lang_column = m.Service.name_ua if query.lang == CFG.UA else m.Service.name_en
                svc_stmt = sa.select(m.Service).where(service_lang_column.ilike(f"%{word}%"))
                if db.execute(svc_stmt).first():
                    stmt = stmt.where(service_lang_column.ilike(f"%{word}%"))
                else:
                    stmt = stmt.where(m.User.fullname.ilike(f"%{word}%"))

    top_users: Sequence[m.User] = db.scalars(stmt.order_by(m.User.average_rate.desc())).all()

    return s.PublicUsersSearchOut(
        lang=query.lang,
        locations=[_ for _ in db_locations],
        selected_locations=query.selected_locations,
        top_users=create_out_search_users(top_users, query.lang, db),
        query=query.query,
    )


def get_public_user_profile(user_uuid: str, lang: Literal[CFG.UA, CFG.EN], db: Session) -> s.PublicUserProfileOut:  # type: ignore
    """Returns user profile"""

    db_user: m.User | None = db.scalar(sa.select(m.User).where(m.User.uuid == user_uuid))
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    services = [
        s.Service(uuid=service.uuid, name=service.name_ua if lang == CFG.UA else service.name_en)
        for service in db_user.services
    ]
    regions: Result[Tuple[str, str]] = db.execute(
        sa.select(m.Region.name_ua if lang == CFG.UA else m.Region.name_en, m.Location.uuid)
        .join(m.Location)
        .join(m.user_locations)
        .where(m.user_locations.c.user_id == db_user.id)
    )
    locations: list[s.LocationStrings] = [s.LocationStrings(name=name, uuid=uuid) for name, uuid in regions]

    return s.PublicUserProfileOut(
        **pop_keys(db_user.__dict__, ["services", "locations"]),
        services=services,
        locations=locations,
        owned_rates_count=db_user.owned_rates_count,
    )
