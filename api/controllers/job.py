from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.engine.result import Result
from sqlalchemy.orm import Session, aliased

import app.models as m
import app.schema as s
from config import config

CFG = config()

service_alias = aliased(m.Service)


def get_jobs_on_home_page(current_user: m.User, query: s.JobHomePage, db: Session) -> s.JobsCardList:
    stmt = sa.select(m.Job).where(
        sa.and_(
            m.Job.is_deleted.is_(False),
            m.Job.is_public.is_(True),
            m.Job.status == s.JobStatus.PENDING,
        )
    )

    recommended_jobs: Sequence[m.Job] = db.scalars(stmt.order_by(m.Job.id)).limit(10).all()
    if query.location_uuid:
        stmt = stmt.join(m.Location).where(m.Location.uuid == query.location_uuid)

    jobs_near_you: Sequence[m.Job] = db.scalars(stmt).limit(10).all()
    user_saved_jobs: Result = db.scalars(sa.select(m.saved_jobs).where(m.saved_jobs.user_id == current_user.id))

    s.JobCard.model_validate
    return s.JobsCardList(
        lang=query.lang,
        recommended_jobs=[
            s.JobCard(
                location=s.LocationStrings(
                    uuid=query.location_uuid,
                    name=job.location.region.name_ua if query.lang == CFG.UA else job.location.region.name_en,
                ),
                is_saved=job.id in user_saved_jobs,
                **job.__dict__,
            )
            for job in recommended_jobs
        ],
        jobs_near_you=[
            s.JobCard(
                location=s.LocationStrings(
                    uuid=query.location_uuid,
                    name=job.location.region.name_ua if query.lang == CFG.UA else job.location.region.name_en,
                ),
                is_saved=job.id in user_saved_jobs,
                **job.__dict__,
            )
            for job in jobs_near_you
        ],
    )


def search_jobs(query: s.JobSearchIn, me: m.User, db: Session) -> s.JobsSearchOut:
    stmt = sa.select(m.Job).where(
        sa.and_(
            m.Job.is_deleted.is_(False),
            m.Job.is_public.is_(True),
            m.Job.status == s.JobStatus.PENDING,
        )
    )

    if query.query:
        stmt = stmt.where(
            sa.or_(
                m.Job.title.ilike(f"%{query.query}%"),
                m.Job.description.ilike(f"%{query.query}%"),
            )
        )

    if query.selected_services:
        stmt = stmt.join(m.job_services).join(service_alias).where(service_alias.name.in_(query.selected_services))

    if query.selected_locations:
        stmt = stmt.join(m.Location).where(m.Location.name_ua.in_(query.selected_locations))

    jobs: Sequence[m.Job] = db.scalars(stmt).all()
    return s.JobsSearchOut(
        lang=query.lang,
        query=query.query,
        jobs=[
            s.JobCard(
                location=s.LocationStrings(
                    uuid=job.location.uuid,
                    name=job.location.region.name_ua if query.lang == CFG.UA else job.location.region.name_en,
                ),
                is_saved=False,
                **job.__dict__,
            )
            for job in jobs
        ],
    )
