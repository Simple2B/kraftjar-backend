from pydantic import BaseModel, ConfigDict, AnyHttpUrl


class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone: str
    email: str
    activated: bool = True

    model_config = ConfigDict(
        from_attributes=True,
    )


class BaseAuth(BaseModel):
    email: str
    first_name: str | None = None
    last_name: str | None = None
    uid: str | None = None
    display_name: str | None = None
    phone: str
    locations: list[int] | None = None
    professions: list[int] | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class GoogleAuth(BaseAuth):
    photo_url: AnyHttpUrl | str | None = None


class AppleAuth(BaseAuth):
    pass
