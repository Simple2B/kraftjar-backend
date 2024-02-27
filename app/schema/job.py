from pydantic import BaseModel, ConfigDict

import enum
from datetime import datetime


class JobStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


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


class JobPut(BaseModel):
    title: str | None = None
    description: str | None = None
    address_id: int | None = None
    location_id: int | None = None
    time: str | None = None
    is_public: bool | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


# schema for created jobs test data
class JobCompletedCreate(BaseModel):
    title: str
    description: str
    address_id: int
    location_id: int | None = None
    time: str = ""
    status: JobStatus
    is_public: bool
    owner_id: int
    worker_id: int | None = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False

    model_config = ConfigDict(
        from_attributes=True,
    )
