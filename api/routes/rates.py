from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import app.models as m
import app.schema as s
from api.dependency import get_current_user
from app.database import get_db

rate_router = APIRouter(prefix="/rates", tags=["rates"])


@rate_router.get("/{rate_id}", status_code=status.HTTP_200_OK, response_model=s.RateOut)
def get_rate(
    rate_id: int,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    pass


@rate_router.get("/", status_code=status.HTTP_200_OK, response_model=s.RateOutList)
def get_rates(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    pass


@rate_router.post("/", status_code=status.HTTP_201_CREATED, response_model=s.RateOut)
def create_rate(
    rate: s.RateIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    pass


@rate_router.put("/{rate_id}", status_code=status.HTTP_200_OK, response_model=s.RateOut)
def update_rate(
    rate_id: int,
    rate: s.RateIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    pass
