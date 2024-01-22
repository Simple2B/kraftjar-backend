from datetime import datetime

from pydantic import BaseModel, ConfigDict
from app.models.application import ApplicationStatus, ApplicationType


class ApplicationOut(BaseModel):
    id: int
    uuid: str

    worker_id: int
    job_id: int
    type: ApplicationType
    status: ApplicationStatus

    created_at: datetime
    is_deleted: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class ApplicationOutList(BaseModel):
    data: list[ApplicationOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class ApplicationIn(BaseModel):
    type: ApplicationType
    job_id: int
    worker_id: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class ApplicationPut(BaseModel):
    status: ApplicationStatus | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )
