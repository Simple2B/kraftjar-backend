from fastapi import APIRouter, Depends, HTTPException, status
from mypy_boto3_sns import SNSClient
import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from botocore.exceptions import ClientError

from api import controllers as c
from api.dependency import get_current_user, get_sns_connect, get_db
from app import models as m
from app import schema as s
from app.logger import log
from config import config

router = APIRouter(prefix="/registration", tags=["Registration"])

CFG = config()


@router.post(
    "/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_406_NOT_ACCEPTABLE: {"description": "This phone is already registered"},
        status.HTTP_409_CONFLICT: {"description": "This email is already registered"},
    },
)
def register_user(
    auth_data: s.RegistrationIn,
    db=Depends(get_db),
    sns_client: SNSClient = Depends(get_sns_connect),
):
    """Logs in a user"""
    log(log.INFO, "Register user with phone [%s]", auth_data.phone)
    return c.register_user(
        auth_data,
        db,
        sns_client,
    )


@router.post(
    "/phone_verification",
    status_code=status.HTTP_200_OK,
    response_model=s.Token,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User phone not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Phone validation failed"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid OTP code"},
    },
)
def phone_verification(
    phone_data: s.PhoneVerificationIn,
    db=Depends(get_db),
):
    """Logs in a user, returns access token"""
    log(log.INFO, "Phone verification for user with phone [%s]", phone_data.phone)

    return c.verify_phone(phone_data, db)


@router.post(
    "/resend_otp",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
)
def resend_otp(
    data: s.SetPhoneIn,
    db=Depends(get_db),
    sns_client: SNSClient = Depends(get_sns_connect),
):
    """Logs in a user, returns access token"""

    user: m.User | None = db.scalar(sa.select(m.User).where(m.User.phone == data.phone))

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        c.send_sms_to_user(user, sns_client, db)

    except ClientError as e:
        log(log.ERROR, "Error sending SMS - [%s]", e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error while sending SMS",
        )
    except SQLAlchemyError as e:
        log(log.ERROR, "Error while creating user - [%s]", e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error while creating user",
        )


@router.post(
    "/forgot-password-send-otp",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        status.HTTP_403_FORBIDDEN: {"description": "User phone is validated already"},
    },
)
def forgot_password_send_otp(
    data: s.SetPhoneIn,
    db=Depends(get_db),
    sns_client: SNSClient = Depends(get_sns_connect),
):
    """user forgot password"""

    user: m.User | None = db.scalar(sa.select(m.User).where(m.User.phone == data.phone))

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        c.send_sms_to_user(user, sns_client, db)

    except ClientError as e:
        log(log.ERROR, "Error sending SMS - [%s]", e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error while sending SMS",
        )
    except SQLAlchemyError as e:
        log(log.ERROR, "Error while creating user - [%s]", e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error while creating user",
        )


@router.post(
    "/forgot-password-new-password",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        status.HTTP_403_FORBIDDEN: {"description": "User phone is not validated"},
    },
)
def forgot_password_new_password(
    data: s.ChangePasswordIn,
    db=Depends(get_db),
):
    """user forgot password"""

    user: m.User | None = db.scalar(sa.select(m.User).where(m.User.phone == data.phone))

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.phone_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User phone is not validated")

    c.change_password(user, data.password, db)


# reset password
# @router.post(
#     "/reset-password",
#     status_code=status.HTTP_200_OK,
#     responses={
#         status.HTTP_404_NOT_FOUND: {"description": "User not found"},
#     },
# )
# def reset_password(
#     reset_data: s.ResetPasswordIn,
#     db=Depends(get_db),
# ):
#     """Resets password for a user"""
#     log(log.INFO, "Reset password for user with phone [%s]", reset_data.phone)
#     c.reset_password(reset_data, db)


# ====
@router.post(
    "/set-phone",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"description": "This phone is already registered"},
    },
    response_model=s.SetPhoneOut,
)
def set_phone(
    phone_data: s.SetPhoneIn,
    db=Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Sets phone for a user"""
    log(log.INFO, "Set phone [%s] for user with id [%s]", phone_data.phone, current_user.id)
    c.set_phone(phone_data, current_user, db=db)
    c.send_otp_to_user(current_user, db=db)

    return s.SetPhoneOut(phone=phone_data.phone)


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
