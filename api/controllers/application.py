from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.orm import Session

import app.models as m
from config import config
from app.logger import log


CFG = config()


def reject_other_not_accepted_applications(db: Session, application: m.Application):
    """Reject all other applications for the same job."""

    job_applications: Sequence[m.Application] = db.scalars(
        sa.select(m.Application).where(
            m.Application.job_id == application.job_id,
            m.Application.status == m.ApplicationStatus.PENDING,
            m.Application.id != application.id,
        )
    ).all()

    if job_applications:
        for job_app in job_applications:
            job_app.status = m.ApplicationStatus.REJECTED

    log(log.INFO, "Rejected applications count: [%s]", len(job_applications))
