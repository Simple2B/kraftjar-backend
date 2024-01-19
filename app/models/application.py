from datetime import datetime
from uuid import uuid4
import enum

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db

from .utils import ModelMixin


class ApplicationType(enum.Enum):
    INVITE = "invite"
    APPLY = "apply"


class ApplicationStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Application(db.Model, ModelMixin):
    __tablename__ = "applications"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    worker_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("users.id"))
    job_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("jobs.id"))

    type: orm.Mapped[ApplicationType] = orm.mapped_column(sa.Enum(ApplicationType))
    status: orm.Mapped[ApplicationStatus] = orm.mapped_column(
        sa.Enum(ApplicationStatus), default=ApplicationStatus.PENDING
    )

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
        return f"<Application {self.id}: worker {self.worker_id} -> job {self.job_id} ({self.type})>"
