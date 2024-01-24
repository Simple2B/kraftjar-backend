from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db

from .utils import ModelMixin
from .service_fields import field_services

if TYPE_CHECKING:
    from .service import Service


class Field(db.Model, ModelMixin):
    __tablename__ = "fields"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    name_en: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False)
    name_ua: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False)

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

    services: orm.Mapped[list["Service"]] = orm.relationship(
        secondary=field_services,
    )

    def __repr__(self):
        return f"<Profession {self.id} {self.name_en} >"

    @property
    def services_count(self):
        return len(self.services)
