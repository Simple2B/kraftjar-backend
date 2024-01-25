from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import app.models as m
import app.schema as s
from api.dependency import get_current_user
from app.database import get_db

service_router = APIRouter(prefix="/services", tags=["service"])


@service_router.post("/", status_code=status.HTTP_200_OK, response_model=s.ServicesOut)
def update_services(
    rate: s.RateIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    pass
