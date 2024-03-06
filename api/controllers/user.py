import re
from typing import Sequence, Tuple

import sqlalchemy as sa
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
        locations: list[s.Location] = [s.Location(name=name, uuid=uuid) for name, uuid in regions]
        users.append(
            s.UserSearchOut(
                **pop_keys(db_user.__dict__, ["services", "locations"]),
                services=services,
                locations=locations,
                owned_rates_count=db_user.owned_rates_count,
                owned_rates_median=db_user.owned_rates_median,
            )
        )
    return users


def search_users(query: s.UserSearchIn, me: m.User, db: Session) -> s.UsersSearchOut:
    """filters users"""

    db_regions: Result[Tuple[str, str]] = db.execute(
        sa.select(m.Region.name_ua if query.lang == CFG.UA else m.Region.name_en, m.Location.uuid)
        .join(m.Location)
        .join(m.user_locations)
        .where(m.user_locations.c.user_id == me.id)
    )

    all_db_locations = db.execute(
        sa.select(m.Region.name_ua if query.lang == CFG.UA else m.Region.name_en, m.Location.uuid).join(m.Location)
    )

    db_locations: set[s.Location] = {s.Location(uuid=uuid, name=name) for name, uuid in all_db_locations}

    user_locations: set[s.Location] = {s.Location(uuid=uuid, name=name) for name, uuid in db_regions}

    db_locations -= user_locations

    stmt = sa.select(m.User).where(m.User.is_deleted.is_(False))

    if query.query:
        wordList = re.sub(CFG.RE_WORD, " ", query.query).split()
        for word in wordList:
            if len(word) >= 3:
                service_lang_column = m.Service.name_ua if query.lang == CFG.UA else m.Service.name_en
                svc_stmt = sa.select(m.Service).where(service_lang_column.ilike(f"%{word}%"))
                if db.execute(svc_stmt).first():
                    stmt = stmt.join(m.user_services).join(m.Service).where(service_lang_column.ilike(f"%{word}%"))
                else:
                    stmt = stmt.where(m.User.fullname.ilike(f"%{word}%"))
    else:
        db_main_services = db.scalars(sa.select(m.Service).where(m.Service.parent_id.is_(None))).all()
        services = {
            s.Service(uuid=service.uuid, name=service.name_ua if query.lang == CFG.UA else service.name_en)
            for service in db_main_services
        }
        stmt = (
            stmt.join(m.user_services).join(m.Service).where(m.Service.uuid.in_([service.uuid for service in services]))
        )

    if query.selected_locations:
        stmt = stmt.join(m.user_locations).join(m.Location)
        if CFG.ALL_UKRAINE in query.selected_locations:
            stmt = stmt.where(m.Location.uuid.in_([location.uuid for location in user_locations]))
        else:
            stmt = stmt.where(m.Location.uuid.in_(query.selected_locations))
        stmt = stmt.order_by(m.User.owned_rates_median.desc())  # type: ignore
        top_users: Sequence[m.User] = db.scalars(stmt.limit(CFG.MAX_USER_SEARCH_RESULTS)).all()
        near_users: Sequence[m.User] = db.scalars(stmt.limit(CFG.MAX_USER_SEARCH_RESULTS)).all()
    else:
        stmt = stmt.order_by(m.User.owned_rates_median.desc())  # type: ignore
        top_users = db.scalars(stmt.limit(CFG.MAX_USER_SEARCH_RESULTS)).all()
        near_users = []

    return s.UsersSearchOut(
        lang=query.lang,
        # services=services,
        locations=[_ for _ in db_locations],
        user_locations=[_ for _ in user_locations],
        # selected_services=query.selected_services,
        selected_locations=query.selected_locations,
        top_users=create_out_search_users(top_users, query.lang, db),
        near_users=create_out_search_users(near_users, query.lang, db),
        query=query.query,
    )
