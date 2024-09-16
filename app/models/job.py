from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from app import schema as s

from .utils import ModelMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .location import Location


class Job(db.Model, ModelMixin):
    __tablename__ = "jobs"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    title: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False)

    description: orm.Mapped[str] = orm.mapped_column(sa.String(1024), nullable=False)

    address_id: orm.Mapped[int | None] = orm.mapped_column(sa.Integer, sa.ForeignKey("addresses.id"))

    start_date: orm.Mapped[datetime | None] = orm.mapped_column(sa.DateTime)

    end_date: orm.Mapped[datetime | None] = orm.mapped_column(sa.DateTime)

    # TODO: may be needed in the future
    # time: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False)

    status: orm.Mapped[str] = orm.mapped_column(sa.Enum(s.JobStatus), default=s.JobStatus.PENDING)

    is_public: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=True)

    is_negotiable: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False, server_default=sa.false())

    is_volunteer: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False, server_default=sa.false())

    cost: orm.Mapped[float | None] = orm.mapped_column(sa.Float)

    location_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("locations.id"), nullable=True)

    owner_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)

    worker_id: orm.Mapped[int | None] = orm.mapped_column(sa.Integer, sa.ForeignKey("users.id"))

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

    location: orm.Mapped["Location"] = orm.relationship()

    def __repr__(self):
        return f"<Job {self.title} - {self.uuid}>"
