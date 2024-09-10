from pydantic import BaseModel, ConfigDict


class WhoAmI(BaseModel):
    uuid: str
    phone_verified: bool

    model_config = ConfigDict(
        from_attributes=True,
    )
