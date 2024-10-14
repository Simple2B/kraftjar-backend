from typing import Sequence
from fastapi import HTTPException, status

import sqlalchemy as sa
from sqlalchemy.orm import Session, aliased

from api.utils import format_location_string
import app.models as m
import app.schema as s
from app.schema.language import Language
from config import config
from app.logger import log

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

    # TODO: Finalize default ordering
    if order_by == s.JobsOrderBy.CREATED_AT:
        users = db.execute(db_jobs.order_by(m.Job.created_at.desc())).scalars().all()
    elif order_by == s.JobsOrderBy.START_DATE:
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


def create_out_search_jobs(db_jobs: Sequence[m.Job], lang: Language, current_user: m.User) -> list[s.JobOutput]:
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
                is_favorite=db_job in current_user.favorite_jobs,
            )
        )
    return jobs


def get_job(job: m.Job, lang: Language, db: Session, job_owner: m.User) -> s.JobInfo:
    ALL_UKRAINE = "Вся Україна" if lang == Language.UA else "All Ukraine"

    service_names = []

    if job.services:
        for service in job.services:
            service_names.append(service.name_ua if lang == Language.UA else service.name_en)

    job_location = ALL_UKRAINE
    if job.location:
        job_location = job.location.region[0].name_ua if lang == Language.UA else job.location.region[0].name_en

    job_address = None
    if job.address:
        lang_name = job.address.line1 if lang == Language.UA else job.address.line2
        lang_type = job.address.street_type_ua if lang == Language.UA else job.address.street_type_en
        job_address = f"{lang_type} {lang_name}"

    # TODO: add files
    files: list[str] = []

    applications: list[s.JobApplication] = []

    if job.applications:
        for application in job.applications:
            worker = db.scalar(sa.select(m.User).where(m.User.id == application.worker_id))
            if not worker:
                log(log.ERROR, "Worker [%s] not found", application.worker_id)
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

            app_location = ALL_UKRAINE

            if worker.locations:
                app_location = (
                    worker.locations[0].region[0].name_ua
                    if lang == Language.UA
                    else worker.locations[0].region[0].name_en
                )

            services = []
            if worker.services:
                for service in worker.services:
                    services.append(service.name_ua if lang == Language.UA else service.name_en)

            applications.append(
                s.JobApplication(
                    uuid=application.uuid,
                    owner=s.JobApplicationOwner(
                        uuid=worker.uuid,
                        fullname=worker.fullname,
                        location=app_location,
                        address=None,
                        services=services,
                        owned_rates_count=round(worker.owned_rates_count, 1),
                        average_rate=round(worker.average_rate, 1),
                    ),
                )
            )

    return s.JobInfo(
        uuid=job.uuid,
        title=job.title,
        location=job_location,
        address=job_address,
        services=service_names,
        owner_name=job_owner.fullname,
        owner_uuid=job_owner.uuid,
        owner_average_rate=job_owner.average_rate,
        owner_rates_count=job_owner.owned_rates_count,
        start_date=job.start_date,
        end_date=job.end_date,
        cost=job.cost,
        description=job.description,
        files=files,
        is_volunteer=job.is_volunteer,
        is_negotiable=job.is_negotiable,
        worker_uuid=job.worker.uuid if job.worker else None,
        applications=applications,
        status=s.JobStatus(job.status),
    )


def get_pending_jobs(db_jobs: Sequence[m.Job], current_user: m.User, lang: Language, db: Session):
    as_owner_jobs = []
    as_worker_jobs = []

    for job in db_jobs:
        if job.owner_id == current_user.id and job.status == s.JobStatus.PENDING.value:
            job_location, job_address = format_location_string(job.location, job.address, lang)

            as_owner_jobs.append(
                s.JobByStatus(
                    uuid=job.uuid,
                    title=job.title,
                    location=job_location,
                    address=job_address,
                    start_date=job.start_date,
                    end_date=job.end_date,
                    cost=job.cost,
                )
            )

    applications = db.scalars(
        sa.select(m.Application).where(
            m.Application.worker_id == current_user.id, m.Application.status == m.ApplicationStatus.PENDING
        )
    ).all()

    if applications:
        app_jobs_ids = [a.job_id for a in applications]
        jobs = [job for job in db_jobs if job.id in app_jobs_ids]

        for job in jobs:
            job_location, job_address = format_location_string(job.location, job.address, lang)

            as_worker_jobs.append(
                s.JobByStatus(
                    uuid=job.uuid,
                    title=job.title,
                    location=job_location,
                    address=job_address,
                    start_date=job.start_date,
                    end_date=job.end_date,
                    cost=job.cost,
                )
            )

    return (as_owner_jobs, as_worker_jobs)


def get_in_progress_jobs(db_jobs: Sequence[m.Job], current_user: m.User, lang: Language):
    as_owner_jobs = []
    as_worker_jobs = []

    for job in db_jobs:
        if job.owner_id == current_user.id and job.is_in_progress:
            job_location, job_address = format_location_string(job.location, job.address, lang)

            as_owner_jobs.append(
                s.JobByStatus(
                    uuid=job.uuid,
                    title=job.title,
                    location=job_location,
                    address=job_address,
                    start_date=job.start_date,
                    end_date=job.end_date,
                    cost=job.cost,
                )
            )

    for job in db_jobs:
        if job.worker_id == current_user.id and job.is_in_progress:
            job_location, job_address = format_location_string(job.location, job.address, lang)

            as_worker_jobs.append(
                s.JobByStatus(
                    uuid=job.uuid,
                    title=job.title,
                    location=job_location,
                    address=job_address,
                    start_date=job.start_date,
                    end_date=job.end_date,
                    cost=job.cost,
                )
            )

    return (as_owner_jobs, as_worker_jobs)


def get_archived_jobs(db_jobs: Sequence[m.Job], current_user: m.User, lang: Language):
    as_owner_jobs = []
    as_worker_jobs = []

    for job in db_jobs:
        if (
            job.owner_id == current_user.id
            and job.status == s.JobStatus.COMPLETED.value
            or job.status == s.JobStatus.CANCELED.value
        ):
            job_location, job_address = format_location_string(job.location, job.address, lang)

            as_owner_jobs.append(
                s.JobByStatus(
                    uuid=job.uuid,
                    title=job.title,
                    location=job_location,
                    address=job_address,
                    start_date=job.start_date,
                    end_date=job.end_date,
                    cost=job.cost,
                )
            )

    for job in db_jobs:
        if (
            job.worker_id == current_user.id
            and job.status == s.JobStatus.COMPLETED.value
            or job.status == s.JobStatus.CANCELED.value
        ):
            job_location, job_address = format_location_string(job.location, job.address, lang)

            as_worker_jobs.append(
                s.JobByStatus(
                    uuid=job.uuid,
                    title=job.title,
                    location=job_location,
                    address=job_address,
                    start_date=job.start_date,
                    end_date=job.end_date,
                    cost=job.cost,
                )
            )

    return (as_owner_jobs, as_worker_jobs)
