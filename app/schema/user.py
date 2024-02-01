from pydantic import BaseModel, ConfigDict
from typing import Sequence

from .service import ServiceDB


class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone: str
    email: str
    is_deleted: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserFile(BaseModel):
    fullname: str
    phone: str
    email: str
    password: str
    location_ids: list[int] = []
    service_ids: list[int] = []
    is_volunteer: bool = False


class UsersFile(BaseModel):
    users: list[UserFile]


class UserSearchOut(BaseModel):
    services: list[ServiceDB] = []
    users: list[User] = []


class UserList(BaseModel):
    users: Sequence[User]

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserFilters(BaseModel):
    services: list[str] = []
    locations: list[str] = []
    q: str = ""
