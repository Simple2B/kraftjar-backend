import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from config import config

from .test_data import TestData

CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_services(client: TestClient, headers: list[dict[str, str]], test_data: TestData, db: Session):
    pass
