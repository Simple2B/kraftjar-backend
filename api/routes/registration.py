from fastapi import APIRouter, Depends, status

from api import controllers as c
from api.dependency import get_current_user, get_db
from app import models as m
from app import schema as s
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


@router.post(
    "/set-phone",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"description": "This phone is already registered"},
    },
)
def set_phone(phone_data: s.SetPhoneIn, db=Depends(get_db), current_user: m.User = Depends(get_current_user)):
    """Sets phone for a user"""
    log(log.INFO, "Set phone [%s] for user with id [%s]", phone_data.phone, current_user.id)
    c.set_phone(phone_data, current_user, db=db)
    c.send_otp_to_user(current_user, db=db)


@router.post(
    "/validate-phone",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_409_CONFLICT: {"description": "Phone validation failed"},
        status.HTTP_403_FORBIDDEN: {"description": "User phone is validated already"},
        status.HTTP_406_NOT_ACCEPTABLE: {"description": "User phone not found"},
    },
)
def validate_phone(phone_data: s.ValidatePhoneIn, db=Depends(get_db), current_user: m.User = Depends(get_current_user)):
    """Sets phone for a user"""
    log(log.INFO, "Set phone [%s] for user with id [%s]", current_user.phone, current_user.id)
    c.validate_phone(current_user, phone_data.code, db=db)


@router.get(
    "/set-otp",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "User phone is already validated"},
        status.HTTP_406_NOT_ACCEPTABLE: {"description": "User phone not found"},
    },
)
def set_otp(db=Depends(get_db), current_user: m.User = Depends(get_current_user)):
    """Sets phone for a user"""
    log(log.INFO, "Set phone [%s] for user with id [%s]", current_user.phone, current_user.id)
    c.send_otp_to_user(current_user, db=db)
