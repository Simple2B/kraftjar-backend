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


class GoogleAuth(BaseModel):
    email: str
    first_name: str | None = None
    last_name: str | None = None
    photo_url: AnyHttpUrl | str | None
    uid: str | None
    display_name: str | None
    phone: str | None
    locations: list[int] | None
    professions: list[int] | None

    model_config = ConfigDict(
        from_attributes=True,
    )
