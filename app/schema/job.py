import enum
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from config import config

from .location import LocationStrings

CFG = config()


class JobStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class BaseJob(BaseModel):
    id: int
    uuid: str
    title: str
    address_id: int | None = None
    location_id: int | None = None
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
    address_id: int | None = None
    location_id: int | None = None
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
    lang: str | None = CFG.UA
    query: str | None = ""

    selected_services: list[str] = []
    selected_locations: list[str] = []


class JobSearch(BaseModel):
    id: int
    uuid: str
    title: str
    description: str
    location: LocationStrings
    cost: int
    is_saved: bool


class JobsSearchOut(BaseModel):
    lang: str | None = CFG.UA
    query: str | None = ""
    jobs: list[JobSearch] = []


class JobHomePage(BaseModel):
    lang: str | None = CFG.UA
    location_uuid: str | None = None


class JobCard(BaseModel):
    id: int
    uuid: str
    title: str
    description: str
    location: LocationStrings
    cost: int
    is_saved: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class JobsCardList(BaseModel):
    lang: str | None = CFG.UA

    location_uuid: str | None = None
    recommended_jobs: list[JobCard] = []
    jobs_near_you: list[JobCard] = []


# schema for created jobs test data
class JobCompletedCreate(BaseModel):
    title: str
    description: str
    address_id: int | None = None
    location_id: int | None = None
    time: str | None = ""
    status: JobStatus
    is_public: bool
    owner_id: int
    worker_id: int | None = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False
    rate_worker: int
    rate_owner: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class JobsFile(BaseModel):
    jobs: list[JobCompletedCreate]

    model_config = ConfigDict(
        from_attributes=True,
    )


class PublicJobStatistics(BaseModel):
    jobs_count: int
    experts_count: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class PublicJobDict(BaseModel):
    statistics: dict[int | None, PublicJobStatistics]

    model_config = ConfigDict(
        from_attributes=True,
    )
