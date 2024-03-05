from typing import Sequence, Tuple

import sqlalchemy as sa
from sqlalchemy.engine.result import Result
from sqlalchemy.orm import Session, aliased

import app.models as m
import app.schema as s
from app.logger import log
from config import config

from app.utilities import pop_keys

CFG = config()


service_alias = aliased(m.Service)


def get_search_users(db_users: Sequence[m.User], lang: str, db: Session) -> list[s.UserSearchOut]:
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

    user_locations_subquery = (
        sa.select(m.Location.uuid).join(m.user_locations).where(m.user_locations.c.user_id == me.id)
    )

    main_query = (
        sa.select(m.Region.name_ua if query.lang == CFG.UA else m.Region.name_en, m.Location.uuid)
        .join(m.Location, m.Region.location_id == m.Location.id)
        .where(m.Location.uuid.notin_(user_locations_subquery))
    )

    all_db_locations = db.execute(main_query)

    db_locations: list[s.Location] = [
        s.Location(
            uuid=uuid,
            name=name,
        )
        for name, uuid in all_db_locations
    ]

    stmt = sa.select(m.User).where(m.User.is_deleted.is_(False))

    if query.query:
        # search services
        service_lang_column = m.Service.name_ua if query.lang == CFG.UA else m.Service.name_en
        svc_stmt = sa.select(m.Service).where(service_lang_column.ilike(f"%{query.query}%"))
        services = [
            s.Service(uuid=service.uuid, name=service.name_ua if query.lang == CFG.UA else service.name_en)
            for service in db.scalars(svc_stmt).all()
        ]
        services_uuids = [service.uuid for service in services]
        if services_uuids:
            stmt = stmt.join(m.user_services).join(m.Service).where(m.Service.uuid.in_(services_uuids))
        else:
            stmt = stmt.where(m.User.fullname.ilike(f"%{query.query}%"))
    else:
        # query string is empty
        db_main_services = db.scalars(sa.select(m.Service).where(m.Service.parent_id.is_(None))).all()
        # get only main services
        services = [
            s.Service(uuid=service.uuid, name=service.name_ua if query.lang == CFG.UA else service.name_en)
            for service in db_main_services
        ]
        services_uuids = [service.uuid for service in services]
        stmt = stmt.join(m.user_services).join(m.Service).where(m.Service.uuid.in_(services_uuids))

    top_users: Sequence[m.User] = db.scalars(stmt.distinct().limit(CFG.MAX_USER_SEARCH_RESULTS)).all()

    near_users: Sequence[m.User] = db.scalars(stmt.distinct().limit(CFG.MAX_USER_SEARCH_RESULTS)).all()

    if query.selected_locations:
        if CFG.ALL_UKRAINE in query.selected_locations:
            stmt_top_users = stmt.join(m.user_locations).join(m.Location)
            top_users = db.scalars(stmt_top_users.distinct().limit(CFG.MAX_USER_SEARCH_RESULTS)).all()

            user_locations_ids = [location.uuid for location in db_locations]

            stmt_near_users = (
                stmt.join(m.user_locations).join(m.Location).where(m.Location.uuid.in_(user_locations_ids))
            )
            near_users = db.scalars(stmt_near_users.distinct().limit(CFG.MAX_USER_SEARCH_RESULTS)).all()
        else:
            stmt = stmt.join(m.user_locations).join(m.Location).where(m.Location.uuid.in_(query.selected_locations))
            top_users = db.scalars(stmt.distinct().limit(CFG.MAX_USER_SEARCH_RESULTS)).all()
            near_users = []

    log(log.INFO, "Top users [%s]", top_users)
    log(log.INFO, "Near users [%s]", near_users)

    return s.UsersSearchOut(
        lang=query.lang,
        # services=services,
        locations=db_locations,
        user_locations=db_locations,
        # selected_services=query.selected_services,
        selected_locations=query.selected_locations,
        top_users=get_search_users(top_users, query.lang, db),
        near_users=get_search_users(near_users, query.lang, db),
        query=query.query,
    )
