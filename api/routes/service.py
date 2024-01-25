from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import app.schema as s
from api import controllers as c
from app.database import get_db

service_router = APIRouter(prefix="/services", tags=["service"])


@service_router.post(
    "",
    status_code=status.HTTP_200_OK,
    response_model=s.ServicesOut,
)
def get_services(query: s.ServicesIn, db: Session = Depends(get_db)):
    return c.get_services(query, db)
