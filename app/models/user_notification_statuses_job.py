from operator import is_
from uuid import uuid4
from datetime import datetime, UTC

import sqlalchemy as sa
from sqlalchemy import orm
import app.schema as s

from app.database import db

from .utils import ModelMixin


class UserNotificationStatusesJob(db.Model, ModelMixin):
    __tablename__ = "user_notification_statuses_job"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    user_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("users.id"))

    name_ua: orm.Mapped[str] = orm.mapped_column(default=s.JobStatus.PENDING.value)

    name_en: orm.Mapped[str] = orm.mapped_column(default=s.JobStatus.PENDING.value)

    is_active: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=True)

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        default=datetime.now(UTC),
    )

    def __repr__(self):
        return f"<{self.id}:{self.name_ua} >"
