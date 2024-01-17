from datetime import datetime
from typing import Self
from uuid import uuid4

import sqlalchemy as sa
from flask_login import AnonymousUserMixin, UserMixin
from sqlalchemy import orm
from werkzeug.security import check_password_hash, generate_password_hash

from app import schema as s
from app.database import db
from app.logger import log

from .utils import ModelMixin


class User(db.Model, UserMixin, ModelMixin):
    __tablename__ = "users"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    first_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), default="")
    last_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), default="")

    email: orm.Mapped[str] = orm.mapped_column(
        sa.String(128),
    )

    phone: orm.Mapped[str] = orm.mapped_column(sa.String(32), unique=True, nullable=False)

    google_id: orm.Mapped[str] = orm.mapped_column(sa.String(128), default="")
    apple_id: orm.Mapped[str] = orm.mapped_column(sa.String(128), default="")
    diia_id: orm.Mapped[str] = orm.mapped_column(sa.String(128), default="")

    password_hash: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        default=datetime.utcnow,
    )

    updated_at: orm.Mapped[sa.DateTime] = orm.mapped_column(
        sa.DateTime,
        default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    is_deleted: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, server_default=sa.false())

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    @classmethod
    def authenticate(
        cls,
        user_id,
        password,
        session: orm.Session | None = None,
    ) -> Self | None:
        if not session:
            session = db.session
        query = cls.select().where(
            (sa.func.lower(cls.phone) == sa.func.lower(user_id)) | (sa.func.lower(cls.email) == sa.func.lower(user_id))
        )
        assert session
        user = session.scalar(query)
        if not user:
            log(log.WARNING, "user:[%s] not found", user_id)
        elif check_password_hash(user.password, password):
            return user
        return None

    @property
    def is_auth_by_google(self):
        return bool(self.google_id)

    @property
    def is_auth_by_apple(self):
        return bool(self.apple_id)

    def __repr__(self):
        return f"<{self.id}: {self.first_name},{self.email}>"

    @property
    def json(self):
        u = s.User.model_validate(self)
        return u.model_dump_json()


class AnonymousUser(AnonymousUserMixin):
    pass
