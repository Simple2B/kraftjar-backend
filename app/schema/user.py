from typing import Sequence
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from enum import Enum

from app.schema.auth import AuthAccount, AuthAccountOut
from app.schema.language import Language

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


class UsersFile(BaseModel):
    users: list[UserFile]


class UserList(BaseModel):
    users: Sequence[User]

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserSearchOut(BaseModel):
    id: int
    uuid: str
    fullname: str
    owned_rates_count: int
    average_rate: float
    services: list[Service]
    locations: list[LocationStrings]

    __hash__ = object.__hash__


class UserSearchIn(BaseModel):
    lang: Language = Language.UA
    selected_locations: list[str] = []  # list of uuids - selected locations
    query: str = ""


class UsersSearchOut(BaseModel):
    lang: Language = Language.UA
    user_locations: list[LocationStrings] = []
    locations: list[LocationStrings] = []
    selected_locations: list[str] = []  # list of uuids - selected locations
    top_users: list[UserSearchOut] = []
    near_users: list[UserSearchOut] = []
    query: str = ""


class UsersOrderBy(Enum):
    NEAR = "near"
    AVERAGE_RATE = "average_rate"
    OWNED_RATES_COUNT = "owned_rates_count"


class UsersIn(BaseModel):
    lang: Language = Language.UA
    selected_locations: list[str] = []  # list of uuids - selected locations
    query: str = ""
    order_by: UsersOrderBy = UsersOrderBy.AVERAGE_RATE
    ascending: bool = True


class UsersOut(BaseModel):
    items: list[UserSearchOut]
    # user_locations: list[LocationStrings] = [] part of /me

    # TODO: must be separated (another endpoint)
    # locations: list[LocationStrings] = []


class UserShortInfo(BaseModel):
    uuid: str
    fullname: str

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


class UserProfileOut(User):
    auth_accounts: list[AuthAccountOut] = []
    owned_rates_count: int
    average_rate: float
    services: list[Service]
    locations: list[LocationStrings]
    completed_jobs_count: int
    announced_jobs_count: int
    favorite_jobs: list[UserFavoriteJob] = []

    __hash__ = object.__hash__

    model_config = ConfigDict(
        from_attributes=True,
    )


class PublicUserProfileOut(BaseModel):
    id: int
    uuid: str
    fullname: str
    owned_rates_count: int
    average_rate: float
    services: list[Service]
    locations: list[LocationStrings]
    created_at: datetime

    __hash__ = object.__hash__


class PublicUsersSearchOut(BaseModel):
    lang: Language = Language.UA
    locations: list[LocationStrings] = []
    selected_locations: list[str] = []  # list of uuids - selected locations
    top_users: list[UserSearchOut] = []
    query: str = ""


class PublicTopExpertsOut(BaseModel):
    top_experts: list[UserSearchOut]


class UserPut(BaseModel):
    fullname: str = ""
    email: EmailStr | str = ""
    description: str = ""
    locations: list[str] = []
    services: list[str] = []
