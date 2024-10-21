import json
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db

from .notification_devices import notification_devices
from .notification_users import notification_users
from .utils import ModelMixin

if TYPE_CHECKING:
    from .device import Device
    from .job import Job
    from .user import User


class PushNotification(db.Model, ModelMixin):
    """
    Device model

    Used to track user devices and their push notification tokens

    """

    __tablename__ = "push_notifications"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(
        sa.String(36), default=lambda: str(uuid4()), server_default=sa.func.uuid()
    )
    title: orm.Mapped[str] = orm.mapped_column(sa.String(512), nullable=False)
    content: orm.Mapped[str] = orm.mapped_column(sa.String(1024), nullable=False)
    meta_data: orm.Mapped[str] = orm.mapped_column(
        sa.String(1024), default="", server_default=""
    )  # JSON string of notification data object
    fcm_id: orm.Mapped[str] = orm.mapped_column(sa.String(512), default="", server_default="")
    n_type: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False)  # one of PushNotificationType enum

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        default=sa.func.now(),
    )
    updated_at: orm.Mapped[datetime] = orm.mapped_column(
        default=sa.func.now(),
        onupdate=sa.func.now(),
    )
    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)

    created_by_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
    job_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("jobs.id"), nullable=True)

    # Relationships
    create_by: orm.Mapped["User"] = orm.relationship("User", backref="created_notifications")

    sent_to: orm.Mapped[list["Device"]] = orm.relationship(secondary=notification_devices)
    read_by: orm.Mapped[list["User"]] = orm.relationship(secondary=notification_users)
    job: orm.Mapped["Job"] = orm.relationship()

    @property
    def device_tokens(self):
        return [device.push_token for device in self.sent_to]

    @property
    def data(self) -> dict[str, str]:
        data = {
            "original_uuid": str(self.uuid),
            "n_type": self.n_type,
            "job_uuid": self.job.uuid,
        }
        if self.meta_data:
            data.update(json.loads(self.meta_data))
        data = {key: str(value) for key, value in data.items()}
        return data

    def __repr__(self):
        return f"<{self.id}:{self.n_type}. Title: {self.title}>"
