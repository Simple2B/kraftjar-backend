from datetime import datetime
from typing import Self
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm
from werkzeug.security import check_password_hash, generate_password_hash

from app.database import db
from app.logger import log

from .utils import ModelMixin


class User(db.Model, ModelMixin):
    __tablename__ = "users"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    first_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), default="")
    last_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), default="")
    fullname: orm.Mapped[str] = orm.mapped_column(sa.String(128), default="")  # fill in registration form

    email: orm.Mapped[str] = orm.mapped_column(sa.String(128))  # fill in registration form

    phone: orm.Mapped[str] = orm.mapped_column(sa.String(32), unique=True)  # fill in registration form

    google_id: orm.Mapped[str] = orm.mapped_column(sa.String(128), default="")
    apple_id: orm.Mapped[str] = orm.mapped_column(sa.String(128), default="")
    diia_id: orm.Mapped[str] = orm.mapped_column(sa.String(128), default="")

    password_hash: orm.Mapped[str | None] = orm.mapped_column(sa.String(256))  # fill in registration form
    created_at: orm.Mapped[datetime] = orm.mapped_column(default=datetime.utcnow)

    updated_at: orm.Mapped[datetime] = orm.mapped_column(default=sa.func.now(), onupdate=sa.func.now())

    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    @classmethod
    def authenticate(
        cls,
        phone: str,
        password: str,
        session: orm.Session,
    ) -> Self | None:
        assert phone and password, "phone and password must be provided"
        query = cls.select().where((sa.func.lower(cls.phone) == sa.func.lower(phone)))
        user = session.scalar(query)
        if not user:
            log(log.WARNING, "user:[%s] not found", phone)
        elif check_password_hash(user.password_hash, password):
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
