from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import app.schema as s
from api import controllers as c
from app.database import get_db

location_router = APIRouter(prefix="/locations", tags=["Location"])


@location_router.post(
    "",
    status_code=status.HTTP_200_OK,
    response_model=s.LocationsOut,
)
def get_locations(query: s.LocationsIn, db: Session = Depends(get_db)):
    return c.get_locations(query, db)
