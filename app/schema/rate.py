from pydantic import BaseModel


class Rate(BaseModel):
    message: str = ""
    job_id: int
    gives_id: int
    receives_id: int


class RateCreate(Rate):
    rate: int
    created_at: str


class RateIn(BaseModel):
    pass


class RateOut(Rate):
    uuid: str
    rate: int
    created_at: str


class RateOutList(BaseModel):
    rates: list[RateOut]
