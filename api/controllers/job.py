from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.orm import Session, aliased

import app.models as m
import app.schema as s
from app.schema.language import Language
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
            m.Job.status == s.JobStatus.PENDING.value,
        )
    )

    recommended_jobs: Sequence[m.Job] = db.scalars(stmt.order_by(m.Job.id)).fetchmany(CARDS_LIMIT)

    if query.location_uuid:
        stmt = stmt.join(m.Location).where(m.Location.uuid == query.location_uuid)

    jobs_near_you: Sequence[m.Job] = db.scalars(stmt).fetchmany(CARDS_LIMIT)
    user_saved_jobs: Sequence[m.Job] = db.scalars(
        sa.select(m.Job).join(m.SavedJob).where(m.SavedJob.user_id == current_user.id)
    ).all()

    recommended_jobs_out = [
        s.JobCard(
            location=s.LocationStrings(
                uuid=job.location.uuid,
                name=job.location.region[0].name_ua if query.lang == CFG.UA else job.location.region[0].name_en,
            ),
            is_saved=job in user_saved_jobs,
            # TODO: remove location from job.__dict__ add like property in Job model
            **pop_keys(job.__dict__, ["location"]),
        )
        for job in recommended_jobs
    ]
    jobs_near_you_out = [
        s.JobCard(
            location=s.LocationStrings(
                uuid=job.location.uuid,
                name=job.location.region[0].name_ua if query.lang == CFG.UA else job.location.region[0].name_en,
            ),
            is_saved=job in user_saved_jobs,
            # TODO: remove location from job.__dict__ add like property in Job model
            **pop_keys(job.__dict__, ["location"]),
        )
        for job in jobs_near_you
    ]

    return s.JobsCardList(
        lang=query.lang,
        recommended_jobs=recommended_jobs_out,
        jobs_near_you=jobs_near_you_out,
    )


def search_jobs(query: s.JobSearchIn, me: m.User, db: Session) -> s.JobsSearchOut:
    stmt = sa.select(m.Job).where(
        sa.and_(
            m.Job.is_deleted.is_(False),
            m.Job.is_public.is_(True),
            m.Job.status == s.JobStatus.PENDING.value,
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
        stmt = stmt.join(m.JobService).join(service_alias).where(service_alias.name.in_(query.selected_services))

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

    result_dict = {
        int(row[0]): s.PublicJobStatistics(jobs_count=row[1], experts_count=row[2])
        for row in result
        if row[0] is not None
    }
    return s.PublicJobDict(statistics=result_dict)


def filter_jobs_by_locations(
    selected_locations: list[str] | None, db: Session, current_user: m.User, db_jobs: sa.Select
):
    if selected_locations:
        if CFG.ALL_UKRAINE in selected_locations:
            return db_jobs

        locations = db.execute(sa.select(m.Location).where(m.Location.uuid.in_(selected_locations))).scalars().all()
        db_jobs = db_jobs.where(m.Job.location.has(m.Location.uuid.in_([loc.uuid for loc in locations])))
    else:
        db_jobs = db_jobs.where(m.Job.location.has(m.Location.uuid.in_([loc.uuid for loc in current_user.locations])))

    return db_jobs


def filter_and_order_jobs(
    query: str, lang: Language, db: Session, current_user: m.User, db_jobs: sa.Select, order_by: s.JobsOrderBy
):
    """Filters and orders users by query params"""

    query = query.strip()

    if query:
        if lang == Language.UA:
            search_by_service = m.Job.services.any(m.Service.name_ua.ilike(f"%{query}%"))
        else:
            search_by_service = m.Job.services.any(m.Service.name_en.ilike(f"%{query}%"))

        db_jobs = db_jobs.where(sa.or_(m.Job.title.ilike(f"%{query}%"), search_by_service))

    if order_by == s.JobsOrderBy.START_DATE:
        users = db.execute(db_jobs.order_by(m.Job.start_date.desc())).scalars().all()
    elif order_by == s.JobsOrderBy.COST:
        users = db.execute(db_jobs.order_by(m.Job.cost.desc())).scalars().all()
    elif order_by == s.UsersOrderBy.NEAR:
        users = (
            db.execute(
                db_jobs.order_by(
                    m.Job.location.has(m.Location.id.in_([loc.id for loc in current_user.locations])).desc()
                )
            )
            .scalars()
            .all()
        )
    else:
        users = db.execute(db_jobs).scalars().all()

    return users


def create_out_search_jobs(db_jobs: Sequence[m.Job], lang: Language, db: Session) -> list[s.JobOutput]:
    """Creates list of JobOutput from db jobs"""

    jobs: list[s.JobOutput] = []

    for db_job in db_jobs:
        services = [
            s.Service(uuid=service.uuid, name=service.name_ua if lang == Language.UA else service.name_en)
            for service in db_job.services
        ]

        # None == All Ukraine
        location = None

        if db_job.location is not None:
            location = s.LocationStrings(
                name=db_job.location.region[0].name_ua if lang == Language.UA else db_job.location.region[0].name_en,
                uuid=db_job.location.uuid,
            )

        jobs.append(
            s.JobOutput(
                **pop_keys(db_job.__dict__, ["services", "location"]),
                services=services,
                location=location,
            )
        )
    return jobs
