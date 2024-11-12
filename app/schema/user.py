from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from enum import Enum

from app.schema.auth import AuthAccount, AuthAccountOut
from app.schema.language import Language
from app.schema.misc import OrderType

from .location import LocationStrings
from .service import Service


class User(BaseModel):
    id: int
    uuid: str
    fullname: str
    first_name: str
    last_name: str
    phone: str
    is_deleted: bool
    phone_verified: bool
    description: str
    avatar_url: str | None = None

    is_volunteer: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserFile(BaseModel):
    fullname: str
    first_name: str = ""
    last_name: str = ""
    phone: str
    auth_accounts: list[AuthAccount] = []
    password: str
    location_ids: list[int] = []
    service_ids: list[int] = []
    is_volunteer: bool = False
    avatar_url: str | None = None


class UsersFile(BaseModel):
    users: list[UserFile]


class UserSearchOut(BaseModel):
    id: int
    uuid: str
    fullname: str
    owned_rates_count: int
    avatar_url: str | None = None
    average_rate: float
    services: list[Service]
    locations: list[LocationStrings]
    is_favorite: bool
    receiver_average_rate: float
    created_at: datetime
    lang: Language = Language.UA

    __hash__ = object.__hash__


class UserRateOut(BaseModel):
    uuid: str
    fullname: str
    # TODO: must be add avatar field here later

    __hash__ = object.__hash__


class UsersOrderBy(Enum):
    NEAR = "near"
    AVERAGE_RATE = "average_rate"
    OWNED_RATES_COUNT = "owned_rates_count"


class UsersIn(BaseModel):
    lang: Language = Language.UA
    selected_locations: list[str] = []  # list of uuids - selected locations
    query: str = ""
    order_by: UsersOrderBy = UsersOrderBy.AVERAGE_RATE
    order_type: OrderType = OrderType.ASC
    page: int = 1
    size: int = 10


class UsersOut(BaseModel):
    items: list[UserSearchOut]
    total: int
    page: int
    size: int
    pages: int


class UserShortInfo(BaseModel):
    uuid: str
    fullname: str
    avatar_url: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserFavoriteJob(BaseModel):
    job_uuid: str
    title: str
    location: str
    address: str | None = None
    cost: float | None = None
    start_date: datetime | None = None
    owner: UserShortInfo
    is_volunteer: bool
    is_negotiable: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserFavoriteExpert(BaseModel):
    uuid: str
    fullname: str
    locations: list[str]
    avatar_url: str | None = None


class UserNotificationSettingsIn(BaseModel):
    # job statuses
    is_pending_job_status: bool
    is_approved_job_status: bool
    is_in_progress_job_status: bool
    is_on_confirmation_job_status: bool
    is_payment_confirmed_job_status: bool
    is_completed_job_status: bool
    is_canceled_job_status: bool
    # =================================

    # application statuses
    is_pending_aplication_status: bool
    is_accepted_aplication_status: bool
    is_rejected_aplication_status: bool
    # =================================

    # application types
    is_invite_application_type: bool
    is_apply_application_type: bool
    # =================================

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserJobStatusesNotificationSettings(BaseModel):
    is_pending_job_status: bool
    is_approved_job_status: bool
    is_in_progress_job_status: bool
    is_on_confirmation_job_status: bool
    is_payment_confirmed_job_status: bool
    is_completed_job_status: bool
    is_canceled_job_status: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserApplicationStatusesNotificationSettings(BaseModel):
    is_pending_aplication_status: bool
    is_accepted_aplication_status: bool
    is_rejected_aplication_status: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserApplicationTypesNotificationSettings(BaseModel):
    is_invite_application_type: bool
    is_apply_application_type: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserNotificationSettingsOut(BaseModel):
    is_job_statuses_notification_settings: bool
    job_statuses_notification_settings_flags: UserJobStatusesNotificationSettings

    is_application_statuses_notification_settings: bool
    application_statuse_notifications_settings_flags: UserApplicationStatusesNotificationSettings

    is_application_types_notification_settings: bool
    application_types_notification_flags: UserApplicationTypesNotificationSettings

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserProfileOut(User):
    auth_accounts: list[AuthAccountOut] = []
    owned_rates_count: int
    average_rate: float
    services: list[Service]
    locations: list[LocationStrings]
    completed_jobs_count: int
    announced_jobs_count: int
    favorite_jobs: list[UserFavoriteJob] = []
    favorite_experts: list[UserFavoriteExpert] = []
    created_at: datetime
    avatar_url: str | None = None
    receiver_average_rate: float
    preferred_language: Language = Language.UA

    notification_settings: UserNotificationSettingsOut

    __hash__ = object.__hash__

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserPut(BaseModel):
    fullname: str = ""
    email: EmailStr | str = ""
    description: str = ""
    locations: list[str] = []
    services: list[str] = []
    avatar_url: str | None = None
    preferred_language: Language = Language.UA

    model_config = ConfigDict(
        use_enum_values=True,
    )
