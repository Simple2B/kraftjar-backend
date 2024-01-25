from typing import Sequence, cast

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

import app.models as m
import app.schema as s
from api.dependency import get_current_user
from app.database import get_db
from app.logger import log

service_router = APIRouter(prefix="/services", tags=["service"])


@service_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=s.ServiceList,
)
def get_services(db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    services: Sequence[m.Service] = db.scalars(
        select(m.Service).where(m.Service.is_deleted == False).order_by(m.Service.id)  # noqa E712
    ).all()
    log(log.INFO, "services list (%s) returned", len(services))
    return s.ServiceList(services=cast(list, services))


@service_router.get(
    "/{service_id}",
    status_code=status.HTTP_200_OK,
    response_model=s.Service,
    responses={status.HTTP_409_CONFLICT: {s.NotFound().model_dump()}},  # type: ignore
)
def get_service(service_id: int, db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    service: m.Service | None = db.scalar(
        select(m.Service).where(m.Service.id == service_id, m.Service.is_deleted == False)  # noqa E712
    )
    if not service:
        log(log.INFO, "service (%s) not found", service_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Service not found",
        )
    log(log.INFO, "service (%s) returned", service_id)
    return service


@service_router.get(
    "/{field_id}",
    status_code=status.HTTP_200_OK,
    response_model=s.ServiceList,
    responses={status.HTTP_409_CONFLICT: {s.NotFound().model_dump()}},  # type: ignore
)
def get_filtered_service(
    field_id: int, db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)
):
    field: m.Field | None = db.scalar(
        select(m.Field).where(m.Field.id == field_id, m.Field.is_deleted == False)  # noqa E712
    )
    if not field:
        log(log.INFO, "field (%s) not found", field_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Field not found",
        )
    services: Sequence[m.Service] = db.scalars(
        select(m.Service).where(m.Service.field.id == field_id, m.Service.is_deleted == False)  # noqa E712
    ).all()

    log(log.INFO, "services list (%s) returned", len(services))
    return s.ServiceList(services=cast(list, services))
