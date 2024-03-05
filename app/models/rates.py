from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from config import config

from .utils import ModelMixin

CFG = config()


class Rate(db.Model, ModelMixin):
    __tablename__ = "rates"
    __table_args__ = (
        sa.CheckConstraint(f"rate >= {CFG.MINIMUM_RATE}", name="min_rate_check"),
        sa.CheckConstraint(f"rate <= {CFG.MAXIMUM_RATE}", name="max_rate_check"),
    )

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    message: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False)

    job_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("jobs.id"))
    gives_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("users.id"))
    receiver_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("users.id"))

    rate: orm.Mapped[int] = orm.mapped_column(sa.Integer, nullable=False)

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        default=datetime.utcnow,
    )

    updated_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    def __repr__(self):
        return f"<Rate {self.id} | {self.gives_id} ({self.rate}) -> {self.receiver_id}>)"
