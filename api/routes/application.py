from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import app.models as m
import app.schema as s
from api.dependency import get_current_user
from app.database import get_db
from app.logger import log

application_router = APIRouter(prefix="/applications", tags=["applications"])


@application_router.get("/{application_id}", status_code=status.HTTP_200_OK, response_model=s.ApplicationOut)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    pass


@application_router.get("/", status_code=status.HTTP_200_OK, response_model=s.ApplicationOutList)
def get_applications(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    pass


@application_router.post("/", status_code=status.HTTP_201_CREATED, response_model=s.ApplicationOut)
def create_application(
    application: s.ApplicationIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    pass


@application_router.put("/{application_id}", status_code=status.HTTP_200_OK, response_model=s.ApplicationOut)
def update_application(
    application_id: int,
    application: s.ApplicationIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    pass
