from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseJob(BaseModel):
    id: int
    uuid: str
    title: str
    address_id: int
    location_id: int
    owner_id: int
    worker_id: int | None = None

    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class JobOut(BaseJob):
    description: str
    # owner: UserOut
    # worker: UserOut


class JobOutList(BaseModel):
    jobs: list[JobOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class JobIn(BaseModel):
    title: str
    description: str
    address_id: int
    location_id: int
    time: str
    is_public: bool

    model_config = ConfigDict(
        from_attributes=True,
    )
