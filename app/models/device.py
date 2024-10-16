from typing import TYPE_CHECKING
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db

from .utils import ModelMixin

if TYPE_CHECKING:
    from .user import User


class Device(db.Model, ModelMixin):
    """
    Device model

    Used to track user devices and their push notification tokens

    """

    __tablename__ = "devices"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    device_id: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False)  # Device ID, received from the device
    user_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("users.id"))
    push_token: orm.Mapped[str] = orm.mapped_column(
        sa.String(512), nullable=False
    )  # Push token, received from the device

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        default=sa.func.now(),
    )
    updated_at: orm.Mapped[datetime] = orm.mapped_column(
        default=sa.func.now(),
        onupdate=sa.func.now(),
    )
    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)

    # Relationships
    user: orm.Mapped["User"] = orm.relationship()

    def __repr__(self):
        return f"<{self.id}:{self.device_id}. User: {self.user_id}>"
