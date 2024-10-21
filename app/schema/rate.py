from pydantic import BaseModel, ConfigDict
from app.schema.user import User


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
    receiver: User
    giver: User
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
