import enum
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schema.language import Language
from config import config

from .location import LocationStrings
from .file import FileOut
from .service import Service

CFG = config()


class JobStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    ON_CONFIRMATION = "on_confirmation"
    COMPLETED = "completed"
    CANCELED = "canceled"


class BaseJob(BaseModel):
    id: int
    uuid: str
    title: str
    description: str = ""

    address_id: int | None = None
    location_id: int | None = None

    start_date: datetime | None = None
    end_date: datetime | None = None

    owner_id: int
    worker_id: int | None = None

    status: JobStatus

    is_public: bool
    is_negotiable: bool
    is_volunteer: bool

    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class JobOut(BaseJob):
    files: list[FileOut] = []
    service: Service | None = None


class JobApplicationOwner(BaseModel):
    uuid: str
    fullname: str
    location: str
    address: str | None = None
    services: list[str]
    owned_rates_count: int
    average_rate: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class JobApplication(BaseModel):
    uuid: str
    owner: JobApplicationOwner


class JobInfo(BaseModel):
    uuid: str
    title: str
    location: str
    address: str | None = None
    services: list[str]
    owner_name: str
    owner_uuid: str
    owner_average_rate: float
    owner_rates_count: int
    start_date: datetime | None = None
    end_date: datetime | None = None
    cost: float | None = None
    description: str
    files: list[str]
    is_volunteer: bool
    is_negotiable: bool
    worker_uuid: str | None = None
    applications: list[JobApplication]
    status: JobStatus


class JobOutList(BaseModel):
    jobs: list[JobOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


# create job schema
class JobIn(BaseModel):
    lang: str = CFG.UA

    service_uuid: str
    title: str
    description: str

    settlement_uuid: str | None = None
    address_uuid: str | None = None

    start_date: str | None = None
    end_date: str | None = None

    is_negotiable: bool = False
    is_volunteer: bool = False

    cost: int = 0
    is_public: bool = True

    file_uuids: list[str] = []

    model_config = ConfigDict(
        from_attributes=True,
    )


class JobPut(BaseModel):
    title: str | None = None
    description: str | None = None
    address_id: int | None = None
    location_id: int | None = None
    # time: str | None = None
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
    cost: float
    is_saved: bool
    location: LocationStrings

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
    # time: str | None = ""
    status: JobStatus
    is_public: bool
    owner_id: int
    worker_id: int | None = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False
    rate_worker: int
    rate_owner: int
    start_date: datetime
    end_date: datetime | None = None
    cost: float
    services: list[str] = []

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
    statistics: dict[int, PublicJobStatistics]


class JobsOrderBy(enum.Enum):
    NEAR = "near"
    START_DATE = "start_date"
    COST = "cost"
    CREATED_AT = "created_at"


class JobsIn(BaseModel):
    lang: Language = Language.UA
    selected_locations: list[str] = []  # list of uuids - selected locations
    query: str = ""
    order_by: JobsOrderBy = JobsOrderBy.CREATED_AT
    ascending: bool = True


class JobOutput(BaseModel):
    uuid: str
    title: str
    description: str
    cost: float
    start_date: datetime
    end_date: datetime | None = None
    created_at: datetime
    location: LocationStrings | None = None
    services: list[Service]
    is_favorite: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class JobsOut(BaseModel):
    items: list[JobOutput]


class JobByStatus(BaseModel):
    uuid: str
    title: str
    location: str
    address: str | None = None
    start_date: datetime | None
    end_date: datetime | None = None
    cost: float | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class JobsByStatusList(BaseModel):
    owner: list[JobByStatus]
    worker: list[JobByStatus]
    archived: list[JobByStatus]

    model_config = ConfigDict(
        from_attributes=True,
    )


class JobStatusIn(BaseModel):
    status: JobStatus

    model_config = ConfigDict(
        from_attributes=True,
    )
