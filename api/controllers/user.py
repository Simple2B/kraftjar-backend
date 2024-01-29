import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.sql.base import Executable


import app.models as m
import app.schema as s


def get_users(filters: s.UserFilters, db: Session) -> s.UserList:
    """filters users"""
    stmt: Executable = sa.select(m.User).where(m.User.is_deleted == False)  # noqa: E712
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

    if filters.services:
        stmt = (
            stmt.join(m.user_services, isouter=True)
            .join(m.Service, isouter=True)
            .where(m.Service.uuid.in_(filters.services))
        )

    if filters.locations:
        stmt = (
            stmt.join(m.user_locations, isouter=True)
            .join(m.Location, isouter=True)
            .where(m.Location.uuid.in_(filters.locations))
        )

    users: list[m.User] = db.scalars(stmt.distinct()).all()
    return s.UserList(users=users)
