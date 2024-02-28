from pydantic import BaseModel, ConfigDict

import enum
from datetime import datetime
from .service import CFG
from .location import Location


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
    uuid: str
    title: str
    description: str = ""
    address_id: int
    location_id: int
    time: str | None = None
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


class JobSearchIn(BaseModel):
    lang: str = CFG.UA
    query: str = ""

    # selected_services: list[str] = []  # list of uuids - selected services
    selected_locations: list[str] = []  # list of uuids - selected


class JobsSearchOut(BaseModel):
    lang: str = CFG.UA
    # services: list[Service] = []
    locations: list[Location] = []
    # selected_services: list[str] = []  # list of uuids - selected services
    selected_locations: list[str] = []  # list of uuids - selected locations

    recommended_jobs: list[JobOut] = []
    near_users: list[JobOut] = []
    query: str = ""


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
