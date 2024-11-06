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

    notification_settings = s.UserNotificationSettingsIn(
        # job statuses
        is_pending_job_status=False,
        is_approved_job_status=True,
        is_in_progress_job_status=True,
        is_on_confirmation_job_status=False,
        is_completed_job_status=True,
        is_canceled_job_status=False,
        # =================================
        # application statuses
        is_pending_aplication_status=False,
        is_accepted_aplication_status=True,
        is_rejected_aplication_status=True,
        # =================================
        # application types
        is_invite_application_type=True,
        is_apply_application_type=True,
        # =================================
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
