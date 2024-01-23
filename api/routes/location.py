from typing import Sequence, cast

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

import app.models as m
import app.schema as s
from api.dependency import get_current_user
from app.database import get_db
from app.logger import log

location_router = APIRouter(prefix="/locations", tags=["Location"])


@location_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=s.LocationList,
)
def get_locations(db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    locations: Sequence[m.Location] = db.scalars(
        select(m.Location).where(m.Location.is_deleted == False).order_by(m.Location.id)  # noqa E712
    ).all()
    log(log.INFO, "Locations list (%s) returned", len(locations))
    return s.LocationList(locations=cast(list, locations))
