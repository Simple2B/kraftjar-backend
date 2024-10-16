import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

import app.models as m
import app.schema as s
from config import config

CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_user_device(
    client: TestClient,
    db: Session,
    auth_header: dict[str, str],
):
    user: m.User | None = db.scalar(select(m.User).order_by(m.User.id))
    assert user
    test_device_id = "test_device_id"
    test_push_token = "test_push_token"
    device_in = s.DeviceIn(push_token=test_push_token)
    response = client.put(f"api/devices/{test_device_id}", headers=auth_header, content=device_in.model_dump_json())
    assert response.status_code == status.HTTP_200_OK
    device_out = s.DeviceOut.model_validate(response.json())
    assert device_out.device_id == test_device_id
    assert device_out.push_token == test_push_token

    new_push_token = "new_push_token"
    device_in = s.DeviceIn(push_token=new_push_token)
    response = client.put(f"api/devices/{test_device_id}", headers=auth_header, content=device_in.model_dump_json())
    assert response.status_code == status.HTTP_200_OK
    device_out = s.DeviceOut.model_validate(response.json())
    assert device_out.device_id == test_device_id
    assert device_out.push_token == new_push_token
