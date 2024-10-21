from enum import Enum

from pydantic import BaseModel, ConfigDict


class PushNotificationType(Enum):
    job_created = "job_created"
    job_invite_created = "job_invite_created"
    application_created = "application_created"
    application_accepted = "application_accepted"
    application_rejected = "application_rejected"
    job_started = "job_started"
    job_finished = "job_finished"
    job_confirmed = "job_confirmed"
    job_canceled = "job_canceled"


class PushNotificationOut(BaseModel):
    uuid: str
    n_type: PushNotificationType
    job_title: str
    read_by_me: bool
    job_uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )
