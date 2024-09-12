from typing import Sequence
from datetime import datetime
from pydantic import BaseModel, ConfigDict


from app.schema.auth import AuthAccount, AuthAccountOut
from app.schema.language import Language

from .location import LocationStrings
from .service import Service


class User(BaseModel):
    id: int
    uuid: str
    fullname: str
    phone: str = ""
    is_deleted: bool
    phone_verified: bool

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


class UserProfileOut(User):
    auth_accounts: list[AuthAccountOut] = []
    owned_rates_count: int
    average_rate: float
    services: list[Service]
    locations: list[LocationStrings]

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
