from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import sqlalchemy as sa
from app import models as m
import app.schema as s
from api import controllers as c
from app.database import get_db
from app.schema.language import Language
from config import config

CFG = config()

service_router = APIRouter(prefix="/services", tags=["service"])


@service_router.post(
    "",
    status_code=status.HTTP_200_OK,
    response_model=s.ServicesOut,
)
def get_services(query: s.ServicesIn, db: Session = Depends(get_db)):
    return c.get_services(query, db)


@service_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=s.ServicesList,
)
def get_popular_services(lang: Language = Language.UA, db: Session = Depends(get_db)):
    """Get popular services"""

    db_services = db.scalars(sa.select(m.Service)).all()[: CFG.SERVICES_LIMIT]

    services_out = []

    for service in db_services:
        lang_name = service.name_ua if lang == Language.UA else service.name_en
        services_out.append(s.Service(uuid=service.uuid, name=lang_name))

    return s.ServicesList(services=services_out)
