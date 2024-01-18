from datetime import datetime

from pydantic import BaseModel, ConfigDict
from app import models as m


class ApplicationOut(BaseModel):
    id: int
    uuid: str

    worker_id: int
    job_id: int
    type: m.ApplicationType
    status: m.ApplicationStatus

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
    type: m.ApplicationType
    job_id: int
    worker_id: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class ApplicationPut(BaseModel):
    status: m.ApplicationStatus | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )
