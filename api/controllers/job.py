from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.orm import Session, aliased

import app.models as m
import app.schema as s
from config import config

from app.utilities import pop_keys

CFG = config()
CARDS_LIMIT = 10

service_alias = aliased(m.Service)


def get_jobs_on_home_page(query: s.JobHomePage, current_user: m.User, db: Session) -> s.JobsCardList:
    stmt = sa.select(m.Job).where(
        sa.and_(
            m.Job.is_deleted.is_(False),
            m.Job.is_public.is_(True),
            m.Job.status == s.JobStatus.PENDING,
        )
    )

    recommended_jobs: Sequence[m.Job] = db.scalars(stmt.order_by(m.Job.id)).fetchmany(CARDS_LIMIT)
    if query.location_uuid:
        stmt = stmt.join(m.Location).where(m.Location.uuid == query.location_uuid)

    jobs_near_you: Sequence[m.Job] = db.scalars(stmt).fetchmany(CARDS_LIMIT)
    user_saved_jobs: Sequence[m.Job] = db.scalars(
        sa.select(m.Job).join(m.SavedJob).where(m.SavedJob.user_id == current_user.id)
    ).all()

    return s.JobsCardList(
        lang=query.lang,
        recommended_jobs=[
            s.JobCard(
                location=s.LocationStrings(
                    uuid=job.location.uuid,
                    name=job.location.region[0].name_ua if query.lang == CFG.UA else job.location.region[0].name_en,
                ),
                is_saved=job in user_saved_jobs,
                **pop_keys(job.__dict__, ["location"]),
            )
            for job in recommended_jobs
        ],
        jobs_near_you=[
            s.JobCard(
                location=s.LocationStrings(
                    uuid=job.location.uuid,
                    name=job.location.region[0].name_ua if query.lang == CFG.UA else job.location.region[0].name_en,
                ),
                is_saved=job in user_saved_jobs,
                **pop_keys(job.__dict__, ["location"]),
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
            s.JobSearch(
                location=s.LocationStrings(
                    uuid=job.location.uuid,
                    name=job.location.region[0].name_ua if query.lang == CFG.UA else job.location.region[0].name_en,
                ),
                is_saved=False,
                **pop_keys(job.__dict__, ["location"]),
            )
            for job in jobs
        ],
    )


def job_statistics(db: Session) -> s.PublicJobDict:
    """
    Get statistics for jobs and experts per location
    """

    jobs_count = sa.func.count(m.Job.id)
    experts_count = sa.func.count(sa.func.distinct(m.Job.worker_id))

    stmt = sa.select(m.Job.location_id, jobs_count, experts_count).group_by(m.Job.location_id)
    result = db.execute(stmt).all()

    result_dict = {row[0]: {"jobs_count": row[1], "experts_count": row[2]} for row in result}
    return s.PublicJobDict(statistics=result_dict)
