from datetime import datetime
from typing import TYPE_CHECKING, Self
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm
from werkzeug.security import check_password_hash, generate_password_hash

from app.database import db
from app.logger import log
from app.schema.auth import AuthType
from app.schema.user import User as u
from config import config

from .rates import Rate
from .user_locations import user_locations
from .user_services import user_services
from .favorite_jobs import favorite_jobs
from .favorite_experts import favorite_experts
from .utils import ModelMixin

CFG = config()

if TYPE_CHECKING:
    from .location import Location
    from .service import Service
    from .auth_account import AuthAccount
    from .job import Job
    from .device import Device


class User(db.Model, ModelMixin):
    __table_args__ = (
        sa.CheckConstraint(f"average_rate >= {CFG.MINIMUM_RATE} or average_rate == 0", name="min_rate_check"),
        sa.CheckConstraint(f"average_rate <= {CFG.MAXIMUM_RATE}", name="max_rate_check"),
    )

    rates_as_giver: orm.Mapped[list["Rate"]] = orm.relationship("Rate", foreign_keys=[Rate.gives_id], backref="giver")
    rates_as_receiver: orm.Mapped[list["Rate"]] = orm.relationship(
        "Rate", foreign_keys=[Rate.receiver_id], backref="receiver"
    )

    __tablename__ = "users"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    fullname: orm.Mapped[str] = orm.mapped_column(sa.String(128), default="")  # fill in registration form
    first_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), default="")
    last_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), default="")
    description: orm.Mapped[str] = orm.mapped_column(sa.String(512), default="", server_default="")

    phone: orm.Mapped[str] = orm.mapped_column(sa.String(32), unique=True)  # fill in registration form
    phone_verified: orm.Mapped[bool] = orm.mapped_column(default=False)

    auth_accounts: orm.Mapped[list["AuthAccount"]] = orm.relationship("AuthAccount", backref="user")

    password_hash: orm.Mapped[str | None] = orm.mapped_column(sa.String(256))  # fill in registration form
    created_at: orm.Mapped[datetime] = orm.mapped_column(default=datetime.utcnow)

    updated_at: orm.Mapped[datetime] = orm.mapped_column(default=sa.func.now(), onupdate=sa.func.now())

    is_volunteer: orm.Mapped[bool] = orm.mapped_column(default=False)

    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)

    average_rate: orm.Mapped[float] = orm.mapped_column(sa.Float, default=0)

    # Relationships
    services: orm.Mapped[list["Service"]] = orm.relationship(secondary=user_services)
    locations: orm.Mapped[list["Location"]] = orm.relationship(secondary=user_locations)

    favorite_jobs: orm.Mapped[list["Job"]] = orm.relationship(secondary=favorite_jobs)

    devices: orm.Mapped[list["Device"]] = orm.relationship()

    favorite_experts: orm.Mapped[list["User"]] = orm.relationship(
        "User",
        secondary=favorite_experts,
        primaryjoin=id == favorite_experts.c.user_id,
        secondaryjoin=id == favorite_experts.c.expert_id,
        backref="expert_of",
    )

    @property
    def basic_auth_account(self):
        for acc in self.auth_accounts:
            if acc.auth_type == AuthType.BASIC:
                return acc
        raise ValueError("Basic auth account not found")

    @property
    def google_auth_accounts(self):
        return [acc for acc in self.auth_accounts if acc.auth_type == AuthType.GOOGLE]

    @property
    def apple_auth_accounts(self):
        return [acc for acc in self.auth_accounts if acc.auth_type == AuthType.APPLE]

    @property
    def owned_rates_count(self) -> int:
        return len(self.rates_as_receiver)

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

    def __repr__(self):
        return f"<{self.id}: {self.fullname}>"

    # uses for editing user
    @property
    def json(self):
        user = u.model_validate(self)
        return user.model_dump_json()
