from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db

from .utils import ModelMixin


class Location(db.Model, ModelMixin):
    __tablename__ = "locations"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    name: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False)

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        default=datetime.utcnow,
    )

    updated_at: orm.Mapped[sa.DateTime] = orm.mapped_column(
        sa.DateTime,
        default=sa.func.now,
        onupdate=sa.func.now,
    )
    is_deleted: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False)

    def __repr__(self):
        return f"<Location {self.id} {self.name} >"
