from typing import Self
from datetime import datetime
from uuid import uuid4

from flask_login import UserMixin, AnonymousUserMixin
import sqlalchemy as sa
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash

from app.database import db
from .utils import ModelMixin
from app.logger import log
from app import schema as s


def gen_password_reset_id() -> str:
    return str(uuid4())


class Admin(db.Model, UserMixin, ModelMixin):
    __tablename__ = "admins"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    username: orm.Mapped[str] = orm.mapped_column(sa.String(64), unique=True)
    email: orm.Mapped[str] = orm.mapped_column(sa.String(128), unique=True)
    password_hash: orm.Mapped[str] = orm.mapped_column(sa.String(256))
    created_at: orm.Mapped[datetime] = orm.mapped_column(default=sa.func.now())
    updated_at: orm.Mapped[datetime] = orm.mapped_column(default=sa.func.now(), onupdate=sa.func.now())
    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=sa.false())

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
            (sa.func.lower(cls.username) == sa.func.lower(user_id))
            | (sa.func.lower(cls.email) == sa.func.lower(user_id))
        )
        assert session
        user = session.scalar(query)
        if not user:
            log(log.WARNING, "user:[%s] not found", user_id)
        elif check_password_hash(user.password, password):
            return user
        return None

    def reset_password(self):
        self.password_hash = ""
        self.reset_password_uid = gen_password_reset_id()
        self.save()

    def __repr__(self):
        return f"<{self.id}: {self.username},{self.email}>"

    @property
    def json(self):
        u = s.Admin.model_validate(self)
        return u.model_dump_json()


class AnonymousUser(AnonymousUserMixin):
    pass
