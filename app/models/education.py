from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from .files_education import files_education

from .utils import ModelMixin

from config import config
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .file import File

CFG = config()


class Education(db.Model, ModelMixin):
    __tablename__ = "educations"

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))
    user_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("users.id"))

    institution: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False)
    degree: orm.Mapped[str | None] = orm.mapped_column(sa.String(128), nullable=True)
    specialization: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False)
    start_date: orm.Mapped[datetime] = orm.mapped_column(sa.DateTime, nullable=False)
    end_date: orm.Mapped[datetime | None] = orm.mapped_column(sa.DateTime, nullable=True)
    files: orm.Mapped[list["File"]] = orm.relationship(
        "File",
        secondary=files_education,
    )

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        default=datetime.now(UTC),
    )

    updated_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)

    def __str__(self) -> str:
        return f"<Education: {self.id}>"
