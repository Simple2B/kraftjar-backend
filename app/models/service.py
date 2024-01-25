from typing import Self
from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db

from .utils import ModelMixin


class Service(db.Model, ModelMixin):
    __tablename__ = "services"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    name_ua: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False)
    name_en: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False)
    parent_id: orm.Mapped[int] = orm.mapped_column(default=0)

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

    @property
    def parent(self) -> Self | None:
        if self.parent_id:
            stmt = sa.select(Service).where(Service.id == self.parent_id)
            return db.session.scalar(stmt)

    @property
    def children(self) -> list[Self]:
        stmt = sa.select(Service).where(Service.parent_id == self.id)
        return db.session.execute(stmt).scalars().all()

    def __repr__(self):
        return f"<{self.id}:{self.name_ua}>"
