from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db

from .utils import ModelMixin


class Address(db.Model, ModelMixin):
    __tablename__ = "addresses"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    # From Meest Express Public API
    street_id: orm.Mapped[str] = orm.mapped_column(sa.String(36))
    city_id: orm.Mapped[str] = orm.mapped_column(sa.String(36))

    # name ua
    line1: orm.Mapped[str] = orm.mapped_column(sa.String(255))
    # name en
    line2: orm.Mapped[str] = orm.mapped_column(sa.String(255))

    # вул. парк пл. ст. просп. пров. шосе...
    street_type_ua: orm.Mapped[str] = orm.mapped_column(sa.String(36), server_default="", default="")
    street_type_en: orm.Mapped[str] = orm.mapped_column(sa.String(36), server_default="", default="")

    # it is not use now
    postcode: orm.Mapped[str] = orm.mapped_column(sa.String(255))
    city: orm.Mapped[str] = orm.mapped_column(sa.String(255))

    location_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("locations.id"))

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        default=datetime.utcnow,
    )

    updated_at: orm.Mapped[sa.DateTime] = orm.mapped_column(
        sa.DateTime,
        default=sa.func.now(),
        onupdate=sa.func.now(),
    )
    is_deleted: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False)

    def __repr__(self):
        return f"<{self.id}: {self.line1} >"
