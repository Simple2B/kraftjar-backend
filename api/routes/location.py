from typing import Sequence
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
import sqlalchemy as sa

import app.schema as s
from api import controllers as c
from app import models as m
from app.database import get_db

location_router = APIRouter(prefix="/locations", tags=["Location"])


@location_router.post(
    "",
    status_code=status.HTTP_200_OK,
    response_model=s.LocationsOut,
)
def get_locations(query: s.LocationsIn, db: Session = Depends(get_db)):
    return c.get_locations(query, db)


@location_router.get(
    "/address",
    status_code=status.HTTP_200_OK,
    response_model=s.LocationsOut,
)
def get_address(
    query: str,
    db: Session = Depends(get_db),
):
    """Returns the address"""
    # find address by query

    db_address: Sequence[m.Address] = db.scalars(sa.select(m.Address).where(m.Address.name == query)).all()

    if not db_address:
        return s.LocationsOut(lang="ua", locations=[], selected=[])

    return
