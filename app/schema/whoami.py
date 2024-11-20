from pydantic import BaseModel, ConfigDict


class WhoAmI(BaseModel):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )
