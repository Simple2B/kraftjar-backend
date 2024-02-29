from typing import Sequence, Tuple

import sqlalchemy as sa
from sqlalchemy.engine.result import Result
from sqlalchemy.orm import Session, aliased
from fastapi import HTTPException, status

import app.models as m
import app.schema as s
from app.logger import log
from config import config

CFG = config()


service_alias = aliased(m.Service)


def create_out_search_users(
    db_users: Sequence[m.User], lang: str, selected_services: list[str], db: Session
) -> list[s.UserSearchOut]:
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
                uuid=db_user.uuid,
                fullname=db_user.fullname,
                services=services,
                locations=locations,
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
    locations: list[s.Location] = [
        s.Location(
            uuid=uuid,
            name=name,
        )
        for name, uuid in db_regions
    ]

    stmt = sa.select(m.User).where(m.User.is_deleted.is_(False))
    services: list[s.Service] = []
    if query.query: 
        # search services
        if not query.selected_services:
            service_lang_column = m.Service.name_ua if query.lang == CFG.UA else m.Service.name_en
            svc_stmt = sa.select(m.Service).where(service_lang_column.ilike(f"%{query.query}%"))
            services = [
                s.Service(uuid=service.uuid, name=service.name_ua if query.lang == CFG.UA else service.name_en)
                for service in db.scalars(svc_stmt).all()
            ]

        stmt = stmt.where(
            m.User.fullname.ilike(f"%{query.query}%"),
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
            selected_service: m.Service | None = db.scalar(sa.select(m.Service).where(m.Service.uuid == selected_uuid))
            if not selected_service:
                log(log.ERROR, "Service with uuid [%s] not found", selected_uuid)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Service with uuid [{selected_uuid}] not found",
                )

            if selected_service.parent_id:
                services.append(
                    s.Service(
                        uuid=selected_service.uuid,
                        name=selected_service.name_ua if query.lang == CFG.UA else selected_service.name_en,
                    )
                )

            # add all it's children
            for child in selected_service.children:
                services.append(
                    s.Service(uuid=child.uuid, name=child.name_ua if query.lang == CFG.UA else child.name_en)
                )

    if query.selected_services:
        stmt = stmt.join(m.user_services).join(m.Service).where(m.Service.uuid.in_(query.selected_services))

    if query.selected_locations:
        stmt = stmt.join(m.user_locations).join(m.Location).where(m.Location.uuid.in_(query.selected_locations))

    db_users: Sequence[m.User] = db.scalars(stmt.distinct().limit(CFG.MAX_USER_SEARCH_RESULTS)).all()
    return s.UsersSearchOut(
        lang=query.lang,
        services=services,
        locations=locations,
        selected_services=query.selected_services,
        selected_locations=query.selected_locations,
        top_users=create_out_search_users(db_users, query.lang, query.selected_services, db),
        near_users=create_out_search_users(db_users, query.lang, query.selected_services, db),
        query=query.query,
    )
