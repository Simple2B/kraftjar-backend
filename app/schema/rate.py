from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schema.user import UserRateOut


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
    receiver: UserRateOut
    giver: UserRateOut
    job_uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class RateJobOut(Rate):
    uuid: str
    gives_uuid: str | None = None
    receiver_uuid: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class RateOutList(BaseModel):
    items: list[RateOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class RateUserOut(Rate):
    uuid: str
    gives: UserRateOut
    receiver_uuid: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class RateUserOutList(BaseModel):
    items: list[RateUserOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
