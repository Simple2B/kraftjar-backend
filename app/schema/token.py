from datetime import datetime
from pydantic import BaseModel, ConfigDict, AnyHttpUrl


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int
    exp: datetime


class BaseAuth(BaseModel):
    email: str
    first_name: str | None = None
    last_name: str | None = None
    uid: str
    display_name: str | None = None

    phone: str | None = None
    locations: list[int] = []
    professions: list[int] = []

    model_config = ConfigDict(
        from_attributes=True,
    )


class GoogleAuth(BaseAuth):
    photo_url: AnyHttpUrl | str | None = None


class AppleAuth(BaseAuth):
    pass
