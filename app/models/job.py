from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm

from app import schema as s

from app.database import db

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
    address_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("addresses.id"), nullable=True)
    time: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False)

    status: orm.Mapped[str] = orm.mapped_column(sa.Enum(s.JobStatus), default=s.JobStatus.PENDING)
    is_public: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=True)

    cost: orm.Mapped[float] = orm.mapped_column(sa.Float, nullable=True, default=10)  # TODO: remove default!!!

    location_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("locations.id"), nullable=True)
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

    location: orm.Mapped["Location"] = orm.relationship()

    def __repr__(self):
        return f"<Job {self.id} {self.title} >"

    @classmethod
    def job_statistics(cls, db: orm.Session) -> dict[int, dict[str, int]]:
        """
        Get statistics for jobs and experts per location
        """

        jobs_count = sa.func.count(Job.id)
        experts_count = sa.func.count(sa.func.distinct(Job.worker_id))

        stmt = sa.select(Job.location_id, jobs_count, experts_count).group_by(Job.location_id)
        result = db.execute(stmt).all()

        result_dict = {row[0]: {"jobs_count": row[1], "experts_count": row[2]} for row in result}
        return result_dict
