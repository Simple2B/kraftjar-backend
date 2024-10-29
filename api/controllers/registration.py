import random
import sqlalchemy as sa
from fastapi import HTTPException, status
from api.controllers.oauth2 import create_access_token
from botocore.exceptions import ClientError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import Executable
from mypy_boto3_sns import SNSClient

from app import models as m
from app import schema as s
from app.logger import log


def register_user(
    user_data: s.RegistrationIn,
    db: Session,
    sns_client: SNSClient,
):
    try:
        # validate password
        password = s.RegistrationIn.password_validation(user_data.password)

        # check if phone is already registered
        stmt: Executable = sa.select(m.User).where(m.User.phone == user_data.phone)
        if db.scalar(stmt) is not None:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="This phone is already registered")

        # check if email is already registered
        # email is optional
        if user_data.email:
            stmt = sa.select(m.User).where(
                sa.and_(
                    m.User.auth_accounts.any(m.AuthAccount.email == user_data.email),
                    m.AuthAccount.auth_type == s.AuthType.BASIC,
                )
            )
            if db.scalar(stmt) is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This email is already registered")

        user: m.User = m.User(
            fullname=user_data.fullname,
            phone=user_data.phone,
            auth_accounts=[m.AuthAccount(auth_type=s.AuthType.BASIC, email=user_data.email)],
            password=password,
            is_volunteer=user_data.is_volunteer,
        )
        db.add(user)

        # link user to services
        for service_uuid in user_data.services:
            service: m.Service | None = db.scalar(sa.select(m.Service).where(m.Service.uuid == service_uuid))
            if not service:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service not found")
            user.services.append(service)

        # link user to locations
        for location_uuid in user_data.locations:
            location: m.Location | None = db.scalar(sa.select(m.Location).where(m.Location.uuid == location_uuid))
            if not location:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Location not found")
            user.locations.append(location)

        db.commit()
        db.refresh(user)

        log(log.INFO, "User [%s] was created", user.fullname)

        send_sms_to_user(user, sns_client, db)

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


def send_sms_to_user(user: m.User, sns_client: SNSClient, db: Session) -> None:
    # generate otp code
    otp_code = random.randint(100000, 999999)

    user.otp_code = str(otp_code)
    db.commit()

    res = sns_client.publish(
        PhoneNumber=user.phone,
        Subject="OTP code from Kraftjar",
        Message=f"[Kraftjar] Your OTP code is {otp_code}",
    )

    log(log.ERROR, "Sending SMS AWS - [%s]", res)


def verify_phone(phone_data: s.PhoneVerificationIn, db: Session) -> s.Token:
    user: m.User | None = db.scalar(sa.select(m.User).where(m.User.phone == phone_data.phone))

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.otp_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone validation failed")

    if user.otp_code != phone_data.otp_code:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP code")

    user.phone_verified = True
    user.otp_code = None
    db.commit()
    db.refresh(user)

    return s.Token(access_token=create_access_token(user.id))


def change_password(user: m.User, password: str, db: Session) -> None:
    log(log.INFO, "Changing password for user [%s]", user.phone)

    user.password = s.RegistrationIn.password_validation(password)

    db.commit()
    db.refresh(user)

    log(log.INFO, "Password changed for user [%s]", user.phone)


def set_phone(phone_data: s.SetPhoneIn, user: m.User, db: Session) -> None:
    stmt: Executable = sa.select(m.User).where(m.User.phone == phone_data.phone)
    if db.scalar(stmt) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This phone is already registered")
    user.phone = phone_data.phone
    user.phone_verified = False
    db.commit()


def send_otp_to_user(user: m.User, db: Session) -> None:
    log(log.INFO, "Sending SMS to [%s]", user.phone)
    if not user.phone:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="User phone not found")

    if user.phone_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User phone is validated already")

    log(log.INFO, "SMS sended to [%s]", user.phone)


def validate_phone(user: m.User, code: str, db: Session) -> None:
    log(log.INFO, "Validating phone [%s] with code [%s]", user.phone, code)

    user.phone_verified = True

    db.commit()
