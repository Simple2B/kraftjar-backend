from pydantic import BaseModel, ConfigDict


class WhoAmI(BaseModel):
    uuid: str
    is_auth_by_google: bool
    is_auth_by_apple: bool

    model_config = ConfigDict(
        from_attributes=True,
    )
