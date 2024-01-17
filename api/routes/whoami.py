from fastapi import APIRouter, Depends, status

import app.models as m
import app.schema as s
from api.dependency import get_current_user
from app.logger import log
from config import DevelopmentConfig, ProductionConfig, TestingConfig, config

whoami_router = APIRouter(prefix="/whoami", tags=["Whoami"])

settings: DevelopmentConfig | TestingConfig | ProductionConfig = config()


@whoami_router.get("/user", status_code=status.HTTP_200_OK, response_model=s.WhoAmI)
def whoami(
    current_user: m.User = Depends(get_current_user),
    app_version: str | None = None,
):
    if app_version:
        log(log.INFO, "App version for user [%s]: [%s]", current_user.email, app_version)

    return s.WhoAmI.model_validate(current_user)
