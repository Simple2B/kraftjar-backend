from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db

from .utils import ModelMixin
from typing import TYPE_CHECKING

from config import config

if TYPE_CHECKING:
    from .user import User
    from .job import Job

CFG = config()


class Rate(db.Model, ModelMixin):
    __tablename__ = "rates"

    __table_args__ = (
        sa.CheckConstraint(f"rate >= {CFG.MINIMUM_RATE}", name="min_rate_check"),
        sa.CheckConstraint(f"rate <= {CFG.MAXIMUM_RATE}", name="max_rate_check"),
    )

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    job_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("jobs.id"))

    gives_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("users.id"))

    receiver_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("users.id"))

    rate: orm.Mapped[int] = orm.mapped_column(sa.Integer, nullable=False)

    review: orm.Mapped[str] = orm.mapped_column(sa.String(1000), nullable=True)

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        default=datetime.now(UTC),
    )

    updated_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    job: orm.Mapped["Job"] = orm.relationship()

    receiver: orm.Mapped["User"] = orm.relationship(
        "User",
        foreign_keys=[receiver_id],
        backref="rates",
    )

    giver: orm.Mapped["User"] = orm.relationship(
        "User",
        foreign_keys=[gives_id],
    )

    @property
    def job_uuid(self) -> str:
        return self.job.uuid

    @property
    def receiver_uuid(self) -> str:
        return self.receiver.uuid

    @property
    def gives_uuid(self) -> str:
        return self.giver.uuid

    def __str__(self) -> str:
        return f"User[{self.uuid}] - [{self.rate}] stars"
