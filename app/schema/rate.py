from pydantic import BaseModel, ConfigDict
from app import schema as s


class Rate(BaseModel):
    rate: int
    review: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class RateIn(Rate):
    job_uuid: str
    receiver_uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class RateOut(Rate):
    uuid: str
    receiver: s.User
    giver: s.User
    job: s.BaseJob

    model_config = ConfigDict(
        from_attributes=True,
    )


class RateOutList(BaseModel):
    items: list[RateOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
