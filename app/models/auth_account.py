from datetime import datetime, UTC
import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from app.schema.auth import AuthType
from config import config

from .utils import ModelMixin

CFG = config()


class AuthAccount(db.Model, ModelMixin):
    __tablename__ = "auth_accounts"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    user_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)

    email: orm.Mapped[str] = orm.mapped_column(sa.String(128))

    auth_type: orm.Mapped[str] = orm.mapped_column(sa.Enum(AuthType), default=AuthType.BASIC)
    # Services have their own ID
    oauth_id: orm.Mapped[str] = orm.mapped_column(sa.String(128), default="")

    created_at: orm.Mapped[datetime] = orm.mapped_column(default=datetime.now(UTC))
    updated_at: orm.Mapped[datetime] = orm.mapped_column(default=sa.func.now(), onupdate=sa.func.now())
    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)

    __table_args__ = (sa.UniqueConstraint("email", "auth_type", "user_id", name="uq_email_auth_type_user_id"),)

    def __repr__(self):
        return f"<{self.id}: {self.email}>"
