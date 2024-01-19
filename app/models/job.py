from datetime import datetime

import enum
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db

from .utils import ModelMixin


class JobStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Job(db.Model, ModelMixin):
    __tablename__ = "jobs"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    title: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False)
    description: orm.Mapped[str] = orm.mapped_column(sa.String(512), nullable=False)
    address_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("addresses.id"))
    time: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False)

    status: orm.Mapped[str] = orm.mapped_column(sa.Enum(JobStatus), default=JobStatus.PENDING)
    is_public: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=True)

    location_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("locations.id"))
    owner_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
    worker_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("users.id"), nullable=True)

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
        return f"<Job {self.id} {self.title} >"
