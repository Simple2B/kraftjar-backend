from pydantic import BaseModel, ConfigDict


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


class UserList(BaseModel):
    users: list[User]

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserFilters(BaseModel):
    services: list[str] = []
    locations: list[str] = []
    q: str = ""
