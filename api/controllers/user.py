from typing import Sequence, Tuple

import sqlalchemy as sa
from sqlalchemy.engine.result import Result
from sqlalchemy.orm import Session, aliased

import app.models as m
import app.schema as s
from app.logger import log
from config import config

CFG = config()


service_alias = aliased(m.Service)


def create_out_search_users(db_users: Sequence[m.User], lang: str, db: Session) -> list[s.UserSearchOut]:
    """Creates list of UserSearchOut from db users"""

    users = []
    for db_user in db_users:
        services = [
            s.Service(uuid=service.uuid, name=service.name_ua if lang == CFG.UA else service.name_en)
            for service in db_user.services
        ]
        location_ids = [location.id for location in db_user.locations]
        region_stmt = sa.select(m.Region).where(m.Region.location_id.in_(location_ids))
        db_regions = db.scalars(region_stmt).all()
        locations = [
            s.Location(uuid=region.location.uuid, name=region.name_ua if lang == CFG.UA else region.name_en)
            for region in db_regions
        ]
        users.append(
            s.UserSearchOut(
                uuid=db_user.uuid,
                fullname=db_user.fullname,
                services=services,
                locations=locations,
            )
        )
    return users


def search_users(query: s.UserSearchIn, me: m.User, db: Session) -> s.UsersSearchOut:
    """filters users"""

    # fill locations

    db_regions: Result[Tuple[str, str]] = db.execute(
        sa.select(m.Region.name_ua if query.lang == CFG.UA else m.Region.name_en, m.Location.uuid)
        .join(m.Location)
        .join(m.user_locations)
        .where(m.user_locations.c.user_id == me.id)
    )
    locations: list[s.Location] = [
        s.Location(
            uuid=uuid,
            name=name,
        )
        for uuid, name in db_regions
    ]

    stmt = sa.select(m.User).where(m.User.is_deleted.is_(False))
    services: list[s.Service] = []
    if query.query:
        # search services
        if not query.selected_services:
            if query.lang == CFG.UA:
                svc_stmt = sa.select(m.Service).where(m.Service.name_ua.ilike(f"%{query.query}%"))
            else:
                svc_stmt = sa.select(m.Service).where(m.Service.name_en.ilike(f"%{query.query}%"))
            db_services = db.scalars(svc_stmt).all()
            services = [
                s.Service(uuid=service.uuid, name=service.name_ua if query.lang == CFG.UA else service.name_en)
                for service in db_services
            ]

        stmt = stmt.where(
            m.User.fullname.ilike(f"%{query.query}%"),  # TODO: ITS A BUG
        )
    else:
        # query string is empty
        db_main_services = db.scalars(sa.select(m.Service).where(m.Service.parent_id.is_(None))).all()

        # get only main services
        services = [
            s.Service(uuid=service.uuid, name=service.name_ua if query.lang == CFG.UA else service.name_en)
            for service in db_main_services
        ]

        for selected_uuid in query.selected_services:
            # add selected service
            selected_service = db.scalar(sa.select(m.Service).where(m.Service.uuid == selected_uuid))
            assert selected_service
            if selected_service.parent_id:
                services.append(
                    s.Service(
                        uuid=selected_service.uuid,
                        name=selected_service.name_ua if query.lang == CFG.UA else selected_service.name_en,
                    )
                )
            # add all it's children
            if selected_service:
                for child in selected_service.children:
                    services.append(
                        s.Service(uuid=child.uuid, name=child.name_ua if query.lang == CFG.UA else child.name_en)
                    )
            else:
                log(log.ERROR, "Service with uuid [%s] not found", selected_uuid)

    if query.selected_services:
        stmt = (
            stmt.join(m.user_services, isouter=True)
            .join(m.Service, isouter=True)
            .where(m.Service.uuid.in_(query.selected_services))
        )

    if query.selected_locations:
        stmt = (
            stmt.join(m.user_locations, isouter=True)
            .join(m.Location, isouter=True)
            .where(m.Location.uuid.in_(query.selected_locations))
        )

    db_users: Sequence[m.User] = db.scalars(stmt.distinct().limit(CFG.MAX_USER_SEARCH_RESULTS)).all()
    return s.UsersSearchOut(
        lang=query.lang,
        services=services,
        locations=locations,
        selected_services=query.selected_services,
        selected_locations=query.selected_locations,
        top_users=create_out_search_users(db_users, query.lang, db),
        near_users=create_out_search_users(db_users, query.lang, db),
        query=query.query,
    )
