import enum
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schema.language import Language
from app.schema.misc import OrderType
from app.schema.rate import RateJobOut
from config import config

from .location import LocationStrings
from .file import FileOut, File
from .service import Service

CFG = config()


class JobStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    ON_CONFIRMATION = "on_confirmation"
    COMPLETED = "completed"
    PAYMENT_CONFIRMED = "payment_confirmed"
    CANCELED = "canceled"


class JobUserStatus(enum.Enum):
    OWNER = "owner"
    WORKER = "worker"


class JobVisibility(enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"


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
    avatar_url: str | None = None
    location: str
    address: str | None = None
    services: list[str]
    owned_rates_count: int
    average_rate: float
    receiver_average_rate: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class JobApplication(BaseModel):
    uuid: str
    owner: JobApplicationOwner


class JobRate(BaseModel):
    uuid: str
    rates: list[RateJobOut] = []


class JobSettlement(BaseModel):
    name: str
    uuid: str


class JobAddress(BaseModel):
    name: str
    uuid: str


class JobInfo(BaseModel):
    uuid: str
    title: str
    location: str
    address: str | None = None
    settlement: JobSettlement | None = None
    job_address: JobAddress | None = None
    services: list[str]
    owner_name: str
    owner_uuid: str
    owner_average_rate: float
    owner_rates_count: int
    owner_avatar_url: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    cost: float | None = None
    description: str
    files: list[File]
    is_volunteer: bool
    is_negotiable: bool
    worker_uuid: str | None = None
    worker_name: str | None = None
    worker_average_rate: float | None = None
    worker_avatar_url: str | None = None
    applications: list[JobApplication]
    status: JobStatus
    is_cancel_request: bool = False
    is_public: bool


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
    settlement_uuid: str | None = None
    address_uuid: str | None = None
    services: list[str] | None = None
    is_public: bool | None = None
    is_volunteer: bool | None = None

    cost: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_negotiable: bool | None = None

    file_uuids: list[str] = []

    model_config = ConfigDict(
        from_attributes=True,
    )


class JobPutOut(BaseModel):
    title: str
    description: str
    location: str
    address: str | None = None
    services: list[str]
    is_public: bool
    is_volunteer: bool
    is_negotiable: bool
    start_date: datetime
    end_date: datetime | None = None
    cost: float | None = None

    files: list[File] = []

    model_config = ConfigDict(
        from_attributes=True,
    )


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
    order_type: OrderType = OrderType.ASC
    page: int = 1
    size: int = 10


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
    files: list[File] = []

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
    status: JobStatus
    is_public: bool

    required_rate_owner: bool | None = None
    required_rate_worker: bool | None = None

    files: list[File] = []

    model_config = ConfigDict(
        from_attributes=True,
    )


class JobsByStatusList(BaseModel):
    items: list[JobByStatus]

    model_config = ConfigDict(
        from_attributes=True,
    )


class JobStatusIn(BaseModel):
    status: JobStatus

    model_config = ConfigDict(
        from_attributes=True,
    )


class JobStatusCancelIn(BaseModel):
    status: JobStatus | None

    model_config = ConfigDict(
        from_attributes=True,
    )
