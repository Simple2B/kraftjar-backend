from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db

from .utils import ModelMixin


class Location(db.Model, ModelMixin):
    __tablename__ = "locations"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    def __repr__(self):
        return f"<{self.id}:{self.uuid} >"
