from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from app.schema.service import ServiceDB

from .job_services import job_services

from .utils import ModelMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .job import Job


class Service(db.Model, ModelMixin):
    __tablename__ = "services"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    name_ua: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False)
    name_en: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False)
    parent_id: orm.Mapped[int | None] = orm.mapped_column()

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        default=datetime.utcnow,
    )

    updated_at: orm.Mapped[datetime] = orm.mapped_column(
        default=sa.func.now(),
        onupdate=sa.func.now(),
    )
    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)

    jobs: orm.Mapped[list["Job"]] = orm.relationship("Job", secondary=job_services, back_populates="services")

    @property
    def parent(self) -> ServiceDB | None:
        if not self.parent_id:
            return None
        with db.begin() as session:
            stmt = sa.select(Service).where(Service.id == self.parent_id)
            return ServiceDB.model_validate(session.scalar(stmt))

    @property
    def children(self) -> list[ServiceDB]:
        with db.begin() as session:
            stmt = sa.select(Service).where(Service.parent_id == self.id)
            return [ServiceDB.model_validate(service) for service in session.scalars(stmt).all()]

    def __repr__(self):
        return f"<{self.id}:{self.name_ua}>"
