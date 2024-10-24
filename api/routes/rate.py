from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from fastapi.exceptions import HTTPException
import sqlalchemy as sa

import app.models as m
import app.schema as s
from api.dependency import get_current_user
from app.database import get_db

from app.logger import log

rate_router = APIRouter(prefix="/rates", tags=["rates"])


@rate_router.get(
    "/{rate_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=s.RateOut,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Rate not found"}},
    dependencies=[Depends(get_current_user)],
)
def get_rate(
    rate_uuid: str,
    db: Session = Depends(get_db),
):
    """Get rate by uuid"""

    rate: m.Rate | None = db.scalar(sa.select(m.Rate).where(m.Rate.uuid == rate_uuid))

    if not rate:
        log(log.ERROR, "Rate [%s] not found", rate_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rate not found")

    return rate


@rate_router.get(
    "/{specialist_uuid}/specialist",
    status_code=status.HTTP_200_OK,
    response_model=s.RateUserOutList,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Specialist not found"},
    },
    dependencies=[Depends(get_current_user)],
)
def get_rates(
    specialist_uuid: str,
    db: Session = Depends(get_db),
):
    """Get all rates for specialist user"""

    specialist: m.User | None = db.scalar(sa.select(m.User).where(m.User.uuid == specialist_uuid))

    if not specialist:
        log(log.ERROR, "Specialist [%s] not found", specialist_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specialist not found")

    rates = db.scalars(
        sa.select(m.Rate)
        .where(
            m.Rate.receiver_id == specialist.id,
        )
        .order_by(m.Rate.created_at.desc())
    ).all()

    if not rates:
        log(log.INFO, "Rates not found for user [%s]", specialist.uuid)
        return s.RateUserOutList(items=[])

    rates_out: list[s.RateUserOut] = []

    for rate in rates:
        giver: m.User | None = db.scalar(sa.select(m.User).where(m.User.id == rate.gives_id))

        if not giver:
            log(log.ERROR, "Giver not found for rate [%s]", rate.uuid)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Giver not found")

        receiver: m.User | None = db.scalar(sa.select(m.User).where(m.User.id == rate.receiver_id))

        if not receiver:
            log(log.ERROR, "Receiver not found for rate [%s]", rate.uuid)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receiver not found")

        fullname = giver.fullname if giver.fullname else f"{giver.first_name} {giver.last_name}"

        rate_out = s.RateUserOut(
            rate=rate.rate,
            review=rate.review,
            uuid=rate.uuid,
            gives=s.UserRateOut(
                uuid=giver.uuid,
                fullname=fullname,
            ),
            receiver_uuid=receiver.uuid,
            created_at=rate.created_at,
        )

        rates_out.append(rate_out)

    return s.RateUserOutList(items=rates_out)


@rate_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.RateOut,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Job not found"},
        status.HTTP_403_FORBIDDEN: {"description": "User is not owner or worker of job"},
    },
)
def create_rate(
    data: s.RateIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Create rate for user (owner or worker)"""

    job: m.Job | None = db.scalar(sa.select(m.Job).where(m.Job.uuid == data.job_uuid))

    if not job:
        log(log.ERROR, "Job [%s] not found", data.job_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # check if job has rate from current user like giver
    if job.rates:
        job_giver_ids = [rate.gives_id for rate in job.rates]
        if current_user.id in job_giver_ids:
            log(log.ERROR, "User [%s] already gave rate for job [%s]", current_user.uuid, job.uuid)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User already gave rate for job")

    # Check if current user is owner or worker
    if current_user.id == job.owner_id:
        receiver_id = job.worker_id
        gives_id = job.owner_id
    elif current_user.id == job.worker_id:
        receiver_id = job.owner_id
        gives_id = job.worker_id
    else:
        log(log.ERROR, "User [%s] is not owner or worker of job [%s]", current_user.uuid, job.uuid)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not owner or worker of job")

    # Create rate
    rate = m.Rate(
        rate=data.rate,
        review=data.review,
        gives_id=gives_id,
        receiver_id=receiver_id,
        job_id=job.id,
    )

    db.add(rate)
    db.commit()
    db.refresh(rate)

    log(log.INFO, "Rate [%s] created for job [%s]", rate.uuid, job.uuid)

    job_rate = m.JobRate(rate_id=rate.id, job_id=job.id)
    db.add(job_rate)
    db.commit()
    log(log.INFO, "Rate [%s] added to job [%s]", rate.uuid, job.uuid)

    return rate


@rate_router.put(
    "/{rate_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=s.RateOut,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Rate not found"},
        status.HTTP_403_FORBIDDEN: {"description": "Rate not belongs to user"},
    },
)
def update_rate(
    rate_uuid: str,
    rate: s.RateIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Update rate by uuid"""

    rate_db: m.Rate | None = db.scalar(sa.select(m.Rate).where(m.Rate.uuid == rate_uuid))

    if not rate_db:
        log(log.ERROR, "Rate [%s] not found", rate_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rate not found")

    if rate_db.gives_id != current_user.id:
        log(log.ERROR, "Rate [%s] not belongs to user [%s]", rate_uuid, current_user.uuid)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rate not belongs to user")

    rate_db.rate = rate.rate
    rate_db.review = rate.review

    db.commit()
    db.refresh(rate_db)

    log(log.INFO, "Rate [%s] updated", rate_uuid)

    return rate_db
