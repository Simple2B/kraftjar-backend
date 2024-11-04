import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import schema as s
from config import config

CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_current_user_profile(db: Session, client: TestClient, auth_header: dict):
    # get current user profile
    response = client.get("api/users/me", headers=auth_header)
    assert response.status_code == status.HTTP_200_OK
    data = s.UserProfileOut(**response.json())

    assert data
    assert data.notification_settings

    # update notification settings
    job_statuses = [
        "approved",
        "completed",
        "payment_confirmed",
        "canceled",
    ]

    application_statuses = [
        "accepted",
        "rejected",
    ]

    application_types = [
        "apply",
    ]

    notification_settings = s.UserNotificationSettings(
        notification_change_status_job_flag=True,
        notification_change_statuses_job=job_statuses,
        notification_change_status_application_flag=True,
        notification_change_statuses_application=application_statuses,
        notification_change_type_application_flag=True,
        notification_change_types_application=application_types,
    )

    response = client.patch(
        "api/users/notification-settings",
        json=notification_settings.model_dump(),
        headers=auth_header,
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.UserProfileOut(**response.json())
    assert data
    assert data.notification_settings
    assert len(data.notification_settings.notification_change_statuses_job) == len(job_statuses)
