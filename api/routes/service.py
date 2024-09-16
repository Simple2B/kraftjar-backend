from typing import Sequence

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
import sqlalchemy as sa

import app.schema as s
import app.models as m
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


@service_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[s.Service],
)
def services(
    lang: s.Language = s.Language.UA,
    db: Session = Depends(get_db),
):
    services: Sequence[m.Service] = db.scalars(sa.select(m.Service)).all()

    return [
        s.Service(
            uuid=service.uuid,
            name=service.name_ua if lang == s.Language.UA else service.name_en,
        )
        for service in services
    ]
