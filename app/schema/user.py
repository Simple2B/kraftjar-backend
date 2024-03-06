from pydantic import BaseModel, ConfigDict
from typing import Sequence

from .service import Service, CFG
from .location import Location


class User(BaseModel):
    id: int
    fullname: str
    phone: str
    email: str
    is_deleted: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserFile(BaseModel):
    fullname: str
    first_name: str = ""
    last_name: str = ""
    phone: str
    email: str
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
    owned_rates_median: float
    services: list[Service]
    locations: list[Location]

    __hash__ = object.__hash__


class UserSearchIn(BaseModel):
    lang: str = CFG.UA
    selected_locations: list[str] = []  # list of uuids - selected locations
    query: str = ""


class UsersSearchOut(BaseModel):
    lang: str = CFG.UA
    user_locations: list[Location] = []
    locations: list[Location] = []
    selected_locations: list[str] = []  # list of uuids - selected locations
    top_users: list[UserSearchOut] = []
    near_users: list[UserSearchOut] = []
    query: str = ""
