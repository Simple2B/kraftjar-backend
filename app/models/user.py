from uuid import uuid4
from datetime import datetime, UTC
from typing import TYPE_CHECKING, Self

import sqlalchemy as sa
from sqlalchemy import orm

from werkzeug.security import check_password_hash, generate_password_hash

from app.database import db
from app.logger import log
from app.schema.auth import AuthType
from app.schema.user import User as u
from app import schema as s
from config import config

from .rate import Rate
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
    from .file import File
    from .user_notification_statuses_job import UserNotificationStatusesJob
    from .user_notification_statuses_application import UserNotificationStatusesApplication
    from .user_notification_types_application import UserNotificationTypesApplication


class User(db.Model, ModelMixin):
    __table_args__ = (
        sa.CheckConstraint(f"average_rate >= {CFG.MINIMUM_RATE} or average_rate == 0", name="min_rate_check"),
        sa.CheckConstraint(f"average_rate <= {CFG.MAXIMUM_RATE}", name="max_rate_check"),
    )

    avatar_id: orm.Mapped[int | None] = orm.mapped_column(sa.ForeignKey("files.id"), nullable=True)

    rates_as_giver: orm.Mapped[list["Rate"]] = orm.relationship(
        "Rate",
        foreign_keys=[Rate.gives_id],
        # backref="giver",
    )

    rates_as_receiver: orm.Mapped[list["Rate"]] = orm.relationship(
        "Rate",
        foreign_keys=[Rate.receiver_id],
        # backref="receiver",
    )

    __tablename__ = "users"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    fullname: orm.Mapped[str] = orm.mapped_column(sa.String(128), default="")  # fill in registration form
    first_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), default="")
    last_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), default="")
    description: orm.Mapped[str] = orm.mapped_column(sa.String(512), default="", server_default="")

    phone: orm.Mapped[str] = orm.mapped_column(sa.String(32), unique=True)  # fill in registration form

    otp_code: orm.Mapped[str | None] = orm.mapped_column(sa.String(6), default=None, server_default=None)

    phone_verified: orm.Mapped[bool] = orm.mapped_column(default=False)

    auth_accounts: orm.Mapped[list["AuthAccount"]] = orm.relationship("AuthAccount", backref="user")

    password_hash: orm.Mapped[str | None] = orm.mapped_column(sa.String(256))  # fill in registration form
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        default=datetime.now(UTC),
    )

    updated_at: orm.Mapped[datetime] = orm.mapped_column(default=sa.func.now(), onupdate=sa.func.now())

    is_volunteer: orm.Mapped[bool] = orm.mapped_column(default=False)

    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)

    average_rate: orm.Mapped[float] = orm.mapped_column(sa.Float, default=0)

    # Relationships
    avatar: orm.Mapped["File"] = orm.relationship("File", uselist=False)

    services: orm.Mapped[list["Service"]] = orm.relationship(secondary=user_services)
    locations: orm.Mapped[list["Location"]] = orm.relationship(secondary=user_locations)

    favorite_jobs: orm.Mapped[list["Job"]] = orm.relationship(secondary=favorite_jobs)

    devices: orm.Mapped[list["Device"]] = orm.relationship()

    preferred_language: orm.Mapped[str] = orm.mapped_column(
        sa.String(2), default=s.Language.UA.value, server_default=s.Language.UA.value
    )

    favorite_experts: orm.Mapped[list["User"]] = orm.relationship(
        "User",
        secondary=favorite_experts,
        primaryjoin=id == favorite_experts.c.user_id,
        secondaryjoin=id == favorite_experts.c.expert_id,
        backref="expert_of",
    )

    # notification settings
    notification_change_status_job_flag: orm.Mapped[bool] = orm.mapped_column(
        default=True,
        server_default="true",
    )
    notification_change_statuses_job: orm.Mapped[list["UserNotificationStatusesJob"]] = orm.relationship(
        "UserNotificationStatusesJob",
        backref="user",
    )

    notification_change_status_application_flag: orm.Mapped[bool] = orm.mapped_column(
        default=True,
        server_default="true",
    )
    notification_change_statuses_application: orm.Mapped[
        list["UserNotificationStatusesApplication"]
    ] = orm.relationship(
        "UserNotificationStatusesApplication",
        backref="user",
    )

    notification_change_type_application_flag: orm.Mapped[bool] = orm.mapped_column(
        default=True,
        server_default="true",
    )
    notification_change_types_application: orm.Mapped[list["UserNotificationTypesApplication"]] = orm.relationship(
        "UserNotificationTypesApplication",
        backref="user",
    )

    @property
    def notification_settings(self):
        return s.UserNotificationSettings(
            notification_change_status_job_flag=self.notification_change_status_job_flag,
            notification_change_statuses_job=[
                status.name_ua for status in self.notification_change_statuses_job if status.is_active
            ],
            notification_change_status_application_flag=self.notification_change_status_application_flag,
            notification_change_statuses_application=[
                status.name_ua for status in self.notification_change_statuses_application if status.is_active
            ],
            notification_change_type_application_flag=self.notification_change_type_application_flag,
            notification_change_types_application=[
                status.name_ua for status in self.notification_change_types_application if status.is_active
            ],
        )

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None

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
    def receiver_average_rate(self) -> float:
        if self.owned_rates_count == 0:
            return 0
        return sum([rate.rate for rate in self.rates_as_receiver]) / self.owned_rates_count

    @property
    def active_devices(self):
        return [device for device in self.devices if not device.is_deleted]

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
