from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.orm import Session, aliased

import app.models as m
import app.schema as s


service_alias = aliased(m.Service)


def get_users(filters: s.UserFilters, db: Session) -> s.UserSearchOut:
    """filters users"""
    stmt = sa.select(m.User).where(m.User.is_deleted == False)  # noqa: E712
    services: list[m.Service] = []
    if filters.q:
        stmt = stmt.where(
            sa.or_(
                m.User.first_name.ilike(f"%{filters.q}%"),
                m.User.last_name.ilike(f"%{filters.q}%"),
                m.User.fullname.ilike(f"%{filters.q}%"),
                m.User.email.ilike(f"%{filters.q}%"),
                m.User.phone.ilike(f"%{filters.q}%"),
            )
        )
        services_search: list[int] = db.scalars(
            sa.select(m.Service.id).where(
                sa.or_(m.Service.name_ua.ilike(f"%{filters.q}%"), m.Service.name_en.ilike(f"%{filters.q}%"))
            )
        ).all()
        if services_search:
            stmt = stmt.join(m.user_services, isouter=True).where(m.Service.id.in_(services_search))

    if filters.services:
        stmt = (
            stmt.join(m.user_services, isouter=True)
            .join(m.Service, isouter=True)
            .where(m.Service.uuid.in_(filters.services))
        )

        services = db.scalars(
            sa.select(m.Service)
            .join(service_alias, m.Service.parent_id == service_alias.id)
            .filter(service_alias.uuid.in_(filters.services))
        ).all()

    if filters.locations:
        stmt = (
            stmt.join(m.user_locations, isouter=True)
            .join(m.Location, isouter=True)
            .where(m.Location.uuid.in_(filters.locations))
        )

    users: Sequence[m.User] = db.scalars(stmt.distinct()).all()
    return s.UserSearchOut(users=users, services=services)
