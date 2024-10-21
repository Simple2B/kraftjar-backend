from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from app import schema as s

from .job_services import job_services
from .job_applications import job_applications
from .job_rates import job_rates

from .utils import ModelMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .location import Location
    from .address import Address
    from .user import User
    from .service import Service
    from .application import Application
    from .rate import Rate


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

    status: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=s.JobStatus.PENDING.value)

    is_public: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=True)

    is_negotiable: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False, server_default=sa.false())

    is_volunteer: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False, server_default=sa.false())

    cost: orm.Mapped[float | None] = orm.mapped_column(sa.Float)

    location_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("locations.id"), nullable=True)

    owner_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)

    worker_id: orm.Mapped[int | None] = orm.mapped_column(sa.Integer, sa.ForeignKey("users.id"))

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        default=datetime.now(UTC),
    )

    updated_at: orm.Mapped[sa.DateTime] = orm.mapped_column(
        sa.DateTime,
        default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    is_deleted: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False)

    location: orm.Mapped["Location"] = orm.relationship()
    address: orm.Mapped["Address"] = orm.relationship()

    services: orm.Mapped[list["Service"]] = orm.relationship(
        "Service",
        secondary=job_services,
        back_populates="jobs",
    )

    worker: orm.Mapped["User"] = orm.relationship(
        "User",
        foreign_keys=[worker_id],
        backref="jobs",
    )

    applications: orm.Mapped[list["Application"]] = orm.relationship(secondary=job_applications)

    rates: orm.Mapped[list["Rate"]] = orm.relationship(secondary=job_rates)

    @property
    def is_in_progress(self) -> bool:
        return self.status in [
            s.JobStatus.IN_PROGRESS.value,
            s.JobStatus.APPROVED.value,
            s.JobStatus.ON_CONFIRMATION.value,
        ]

    @property
    def required_rate_worker(self) -> bool:
        rates_givers_ids = [rate.gives_id for rate in self.rates]
        if self.status == s.JobStatus.COMPLETED.value and self.worker_id not in rates_givers_ids:
            return True
        return False

    @property
    def required_rate_owner(self) -> bool:
        rates_givers_ids = [rate.gives_id for rate in self.rates]
        if self.status == s.JobStatus.COMPLETED.value and self.owner_id not in rates_givers_ids:
            return True
        return False

    def __repr__(self):
        return f"<Job {self.title} - {self.uuid}>"
