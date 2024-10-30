import os
from typing import Sequence

import requests
import sqlalchemy as sa
from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicket,
    PushTicketError,
)
from requests.exceptions import ConnectionError, HTTPError
from sqlalchemy.orm import Session as DbSession

# Optionally providing an access token within a session if you have enabled push security
from app import models as m
from app import schema as s
from app.logger import log
from config import config

CFG = config()
session = requests.Session()
session.headers.update(
    {
        "Authorization": f"Bearer {os.getenv('EXPO_TOKEN')}",
        "accept": "application/json",
        "accept-encoding": "gzip, deflate",
        "content-type": "application/json",
    }
)


def send_push_notification(notification: m.PushNotification) -> None:
    try:
        responses: list[PushTicket] = PushClient(session=session).publish_multiple(
            [
                PushMessage(
                    to=device.push_token,
                    body=notification.content,
                    title=notification.title,
                    data=notification.data,
                    priority="high",
                    channel_id="default",
                    sound="default",
                )
                for device in notification.sent_to
            ]
        )
    except PushServerError as exc:
        # Encountered some likely formatting/validation error.
        log(log.ERROR, "[send_push_notification] PushServerError: %s", str(exc.errors))
        return
    except (ConnectionError, HTTPError) as exc:
        log(log.ERROR, "[send_push_notification] ConnectionError or HTTPError: %s", exc)
        return
    except Exception as exc:
        log(log.ERROR, "[send_push_notification] Exception: %s", exc)
        return
    for response in responses:
        try:
            # We got a response back, but we don't know whether it's an error yet.
            # This call raises errors so we can handle them with normal exception
            # flows.
            response.validate_response()

        except DeviceNotRegisteredError as exc:
            # Mark the push token as inactive
            log(log.WARNING, "[send_push_notification] DeviceNotRegisteredError: %s", exc)
        except PushTicketError as exc:
            # Encountered some other per-notification error.
            log(log.ERROR, "[send_push_notification] PushTicketError: %s", exc)


def create_new_job_notification(db: DbSession, job: m.Job) -> m.PushNotification:
    notification = m.PushNotification(
        title="New job available",
        content=f"A new job '{job.title}' is available, check it out!",
        n_type=s.PushNotificationType.job_created.value,
        created_by_id=job.owner_id,
        meta_data="",
        job=job,
    )
    db.add(notification)

    #  get all users whose id is not equal to job owner id and job.location is locations of user

    users = db.scalars(
        sa.select(m.User)
        .join(m.User.locations)
        .filter(
            m.User.id != job.owner_id,
            m.Location.id == job.location_id,
        )
    ).all()

    for user in users:
        notification.sent_to.extend(user.active_devices)
    db.commit()

    return notification


def send_created_job_notification(db: DbSession, job: m.Job) -> None:
    notification = create_new_job_notification(db, job)
    send_push_notification(notification)


# apply application
def create_apply_application_notification(
    db: DbSession,
    job: m.Job,
    worker: m.User,
) -> m.PushNotification:
    fullname = worker.fullname if worker.fullname else f"{worker.first_name} {worker.last_name}"

    notification = m.PushNotification(
        title="New job application",
        content=f"The specialist {fullname} applied for a job '{job.title}'",
        n_type=s.PushNotificationType.application_created.value,
        created_by_id=worker.id,
        meta_data="",
        job=job,
    )

    db.add(notification)

    #  send notification to job owner
    notification.sent_to.extend(job.owner.active_devices)
    db.commit()

    return notification


def send_apply_application_notification(
    db: DbSession,
    job: m.Job,
    worker: m.User,
) -> None:
    notification = create_apply_application_notification(
        db,
        job,
        worker,
    )
    send_push_notification(notification)


# accepted application
def create_accepted_application_notification(
    db: DbSession,
    job: m.Job,
) -> m.PushNotification:
    notification = m.PushNotification(
        title="Application accepted",
        content=f"Your application has been confirmed for job '{job.title}'",
        n_type=s.PushNotificationType.application_accepted.value,
        created_by_id=job.owner_id,
        meta_data="",
        job=job,
    )

    db.add(notification)

    notification.sent_to.extend(job.worker.active_devices)
    db.commit()

    return notification


def send_accepted_application_notification(
    db: DbSession,
    job: m.Job,
) -> None:
    notification = create_accepted_application_notification(
        db,
        job,
    )
    send_push_notification(notification)


# rejected application
def create_rejected_application_notification(
    db: DbSession,
    job: m.Job,
    rejected_applications: Sequence[m.Application],
) -> m.PushNotification:
    notification = m.PushNotification(
        title="Application rejected",
        content=f"Your application has been rejected for job '{job.title}'",
        n_type=s.PushNotificationType.application_rejected.value,
        created_by_id=job.owner_id,
        meta_data="",
        job=job,
    )

    # get user who applied for job and send notification to them, thet owner rejected their application

    users_ids = [app.worker_id for app in rejected_applications]
    users = db.scalars(sa.select(m.User).filter(m.User.id.in_(users_ids))).all()

    for user in users:
        notification.sent_to.extend(user.active_devices)
    db.commit()

    return notification


def send_rejected_application_notification(
    db: DbSession,
    job: m.Job,
    rejected_applications: Sequence[m.Application],
) -> None:
    notification = create_rejected_application_notification(
        db,
        job,
        rejected_applications,
    )
    send_push_notification(notification)


# job started
def create_job_started_notification(
    job: m.Job,
) -> m.PushNotification:
    worker_name = job.worker.fullname if job.worker.fullname else f"{job.worker.first_name} {job.worker.last_name}"
    notification = m.PushNotification(
        title="Job started",
        content=f"Worker {worker_name} started working on '{job.title}'",
        n_type=s.PushNotificationType.job_started.value,
        created_by_id=job.worker_id,
        meta_data="",
        job=job,
    )

    # send notification to job owner
    notification.sent_to.extend(job.owner.active_devices)

    return notification


def send_job_started_notification(
    job: m.Job,
) -> None:
    pass
    notification = create_job_started_notification(job)
    send_push_notification(notification)


# job finished
def create_job_finished_notification(
    job: m.Job,
) -> m.PushNotification:
    worker_name = job.worker.fullname if job.worker.fullname else f"{job.worker.first_name} {job.worker.last_name}"
    notification = m.PushNotification(
        title="Job finished",
        content=f"Worker {worker_name} finished working on '{job.title}'",
        n_type=s.PushNotificationType.job_finished.value,
        created_by_id=job.worker_id,
        meta_data="",
        job=job,
    )

    # send notification to job owner
    notification.sent_to.extend(job.owner.active_devices)

    return notification


def send_job_finished_notification(
    job: m.Job,
) -> None:
    pass
    notification = create_job_finished_notification(job)
    send_push_notification(notification)


# job confirmed
def create_job_confirmed_notification(
    job: m.Job,
) -> m.PushNotification:
    owner_name = job.owner.fullname if job.owner.fullname else f"{job.owner.first_name} {job.owner.last_name}"
    notification = m.PushNotification(
        title="Job accepted",
        content=f"Owner {owner_name} accepted job '{job.title}'",
        n_type=s.PushNotificationType.job_confirmed.value,
        created_by_id=job.owner_id,
        meta_data="",
        job=job,
    )

    # send notification to job worker
    notification.sent_to.extend(job.worker.active_devices)

    return notification


def send_job_confirmed_notification(
    job: m.Job,
) -> None:
    pass
    notification = create_job_confirmed_notification(job)
    send_push_notification(notification)


# job payment confirmed
def create_job_payment_confirmed_notification(
    job: m.Job,
) -> m.PushNotification:
    worker_name = job.worker.fullname if job.worker.fullname else f"{job.worker.first_name} {job.worker.last_name}"
    notification = m.PushNotification(
        title="Payment confirmed",
        content=f"Owner {worker_name} accepted payment job '{job.title}'",
        n_type=s.PushNotificationType.job_payment_received.value,
        created_by_id=job.worker_id,
        meta_data="",
        job=job,
    )

    # send notification to job worker
    notification.sent_to.extend(job.owner.active_devices)

    return notification


def send_job_payment_confirmed_notification(
    job: m.Job,
) -> None:
    pass
    notification = create_job_payment_confirmed_notification(job)
    send_push_notification(notification)


def notification_is_read_by_user(notification: m.PushNotification, user: m.User) -> bool:
    return user in notification.read_by
