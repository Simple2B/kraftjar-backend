from sqlalchemy.orm import Session

from app import models as m
from app import schema as s


def create_user_notification_settings(user: m.User, session: Session):
    """Create notification settings for users"""
    for status in s.JobStatus:
        db_job_status = m.UserNotificationStatusesJob(
            name_ua=status.value,
            name_en=status.value,
            user_id=user.id,
        )
        session.add(db_job_status)
        user.notification_change_statuses_job.append(db_job_status)

    for application_status in m.ApplicationStatus:
        db_application_status = m.UserNotificationStatusesApplication(
            name_ua=application_status.value,
            name_en=application_status.value,
            user_id=user.id,
        )
        session.add(db_application_status)
        user.notification_change_statuses_application.append(db_application_status)

    for application_type in m.ApplicationType:
        db_application_type = m.UserNotificationTypesApplication(
            name_ua=application_type.value,
            name_en=application_type.value,
            user_id=user.id,
        )
        session.add(db_application_type)
        user.notification_change_types_application.append(db_application_type)
