from fastapi import APIRouter, Depends, status

from api.dependency import get_db
from app import schema as s
from api import controllers as c
from app.logger import log
from config import config

router = APIRouter(prefix="/registration", tags=["Registration"])

CFG = config()


@router.post(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=s.Token,
    responses={
        status.HTTP_406_NOT_ACCEPTABLE: {"description": "This phone is already registered"},
        status.HTTP_409_CONFLICT: {"description": "This email is already registered"},
    },
)
def register_user(auth_data: s.RegistrationIn, db=Depends(get_db)):
    """Logs in a user"""
    log(log.INFO, "Register user with phone [%s]", auth_data.phone)
    return c.register_user(auth_data, db)
