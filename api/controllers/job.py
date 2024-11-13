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
                **pop_keys(
                    db_job.__dict__,
                    [
                        "services",
                        "location",
                        "files",
                    ],
                ),
                files=[s.File.model_validate(file) for file in db_job.files],
                services=services,
                location=location,
                is_favorite=db_job in current_user.favorite_jobs,
            )
        )
    return jobs


def get_job(job: m.Job, lang: Language, db: Session, job_owner: m.User, current_user: m.User) -> s.JobInfo:
    ALL_UKRAINE = "Вся Україна" if lang == Language.UA else "All Ukraine"

    service_names = []

    if job.services:
        for service in job.services:
            service_names.append(service.name_ua if lang == Language.UA else service.name_en)

    job_location = ALL_UKRAINE
    if job.address:
        job_settlement_db = db.scalar(sa.select(m.Settlement).where(m.Settlement.city_id == job.address.city_id))
        if not job_settlement_db:
            log(log.ERROR, "Settlement [%s] not found", job.address.city_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settlement not found")

        region_name = job.location.region[0].name_ua if lang == Language.UA else job.location.region[0].name_en
        settlement_name = job_settlement_db.name_ua if lang == Language.UA else job_settlement_db.name_en
        location_type = "м. " if job_settlement_db.type == "CITY" else "с. "
        job_location = f"{location_type}{settlement_name}, {region_name}"

        job_settlement = s.JobSettlement(name=job_location, uuid=job.address.city_id)
    else:
        if job.location:
            location_name = job.location.region[0].name_ua if lang == Language.UA else job.location.region[0].name_en
            job_settlement = s.JobSettlement(name=location_name, uuid=job.location.uuid)

        else:
            job_settlement = None
            location_name = ALL_UKRAINE

    job_address = None
    if job.address:
        lang_name = job.address.line1 if lang == Language.UA else job.address.line2
        lang_type = job.address.street_type_ua if lang == Language.UA else job.address.street_type_en
        job_address = f"{lang_type} {lang_name}"

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
            if application.status == m.ApplicationStatus.PENDING:
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
                            average_rate=round(worker.receiver_average_rate, 1),
                            avatar_url=worker.avatar_url,
                            receiver_average_rate=worker.receiver_average_rate,
                        ),
                    )
                )

    return s.JobInfo(
        uuid=job.uuid,
        title=job.title,
        location=job_location,
        address=job_address,
        settlement=job_settlement,
        job_address=s.JobAddress(name=job_address, uuid=job.address.street_id) if job_address else None,
        services=service_names,
        owner_name=job_owner.fullname,
        owner_uuid=job_owner.uuid,
        owner_average_rate=job_owner.receiver_average_rate,
        owner_rates_count=job_owner.owned_rates_count,
        owner_avatar_url=job_owner.avatar_url,
        start_date=job.start_date,
        end_date=job.end_date,
        cost=job.cost,
        description=job.description,
        files=[s.File.model_validate(file) for file in job.files],
        is_volunteer=job.is_volunteer,
        is_negotiable=job.is_negotiable,
        worker_uuid=job.worker.uuid if job.worker else None,
        worker_name=job.worker.fullname if job.worker else None,
        worker_average_rate=job.worker.receiver_average_rate if job.worker else None,
        worker_avatar_url=job.worker.avatar_url if job.worker else None,
        applications=applications,
        status=s.JobStatus(job.status),
        is_cancel_request=job.is_cancel_request and job.cancel_request_by != current_user.id,
    )


def get_pending_jobs(
    db_jobs: Sequence[m.Job],
    current_user: m.User,
    job_user_status: s.JobUserStatus,
    lang: Language,
    db: Session,
):
    job_out: list[s.JobByStatus] = []

    for job in db_jobs:
        if (
            job.owner_id == current_user.id
            and job.status == s.JobStatus.PENDING.value
            and job_user_status == s.JobUserStatus.OWNER
        ):
            job_location, job_address = format_location_string(job.location, job.address, lang)

            job_out.insert(
                0,
                s.JobByStatus(
                    uuid=job.uuid,
                    title=job.title,
                    location=job_location,
                    address=job_address,
                    start_date=job.start_date,
                    end_date=job.end_date,
                    cost=job.cost,
                    status=s.JobStatus(job.status),
                    required_rate_owner=job.required_rate_owner,
                    required_rate_worker=job.required_rate_worker,
                    files=[s.File.model_validate(file) for file in job.files],
                ),
            )

    applications = db.scalars(
        sa.select(m.Application).where(
            m.Application.is_deleted.is_(False),
            m.Application.worker_id == current_user.id,
            m.Application.status == m.ApplicationStatus.PENDING,
        )
    ).all()

    if applications and job_user_status == s.JobUserStatus.WORKER:
        app_jobs_ids = [a.job_id for a in applications]
        jobs = [job for job in db_jobs if job.id in app_jobs_ids]

        for job in jobs:
            job_location, job_address = format_location_string(job.location, job.address, lang)

            job_out.insert(
                0,
                s.JobByStatus(
                    uuid=job.uuid,
                    title=job.title,
                    location=job_location,
                    address=job_address,
                    start_date=job.start_date,
                    end_date=job.end_date,
                    cost=job.cost,
                    status=s.JobStatus(job.status),
                    required_rate_owner=job.required_rate_owner,
                    required_rate_worker=job.required_rate_worker,
                    files=[s.File.model_validate(file) for file in job.files],
                ),
            )

    return job_out


def get_in_progress_jobs(
    db_jobs: Sequence[m.Job],
    current_user: m.User,
    job_user_status: s.JobUserStatus,
    lang: Language,
):
    jobs_out = []

    if job_user_status == s.JobUserStatus.OWNER:
        for job in db_jobs:
            if job.owner_id == current_user.id and job.is_in_progress:
                job_location, job_address = format_location_string(job.location, job.address, lang)

                jobs_out.append(
                    s.JobByStatus(
                        uuid=job.uuid,
                        title=job.title,
                        location=job_location,
                        address=job_address,
                        start_date=job.start_date,
                        end_date=job.end_date,
                        cost=job.cost,
                        status=s.JobStatus(job.status),
                        required_rate_owner=job.required_rate_owner,
                        required_rate_worker=job.required_rate_worker,
                        files=[s.File.model_validate(file) for file in job.files],
                    )
                )

    if job_user_status == s.JobUserStatus.WORKER:
        for job in db_jobs:
            if job.worker_id == current_user.id and job.is_in_progress:
                job_location, job_address = format_location_string(job.location, job.address, lang)

                jobs_out.append(
                    s.JobByStatus(
                        uuid=job.uuid,
                        title=job.title,
                        location=job_location,
                        address=job_address,
                        start_date=job.start_date,
                        end_date=job.end_date,
                        cost=job.cost,
                        status=s.JobStatus(job.status),
                        required_rate_owner=job.required_rate_owner,
                        required_rate_worker=job.required_rate_worker,
                        files=[s.File.model_validate(file) for file in job.files],
                    )
                )

    return jobs_out


def get_archived_jobs(
    db_jobs: Sequence[m.Job],
    current_user: m.User,
    job_user_status: s.JobUserStatus,
    lang: Language,
):
    jobs_out = []

    if job_user_status == s.JobUserStatus.OWNER:
        for job in db_jobs:
            if job.owner_id == current_user.id and (
                job.status == s.JobStatus.PAYMENT_CONFIRMED.value or job.status == s.JobStatus.CANCELED.value
            ):
                job_location, job_address = format_location_string(job.location, job.address, lang)

                jobs_out.append(
                    s.JobByStatus(
                        uuid=job.uuid,
                        title=job.title,
                        location=job_location,
                        address=job_address,
                        start_date=job.start_date,
                        end_date=job.end_date,
                        cost=job.cost,
                        status=s.JobStatus(job.status),
                        required_rate_owner=job.required_rate_owner,
                        required_rate_worker=job.required_rate_worker,
                        files=[s.File.model_validate(file) for file in job.files],
                    )
                )

    if job_user_status == s.JobUserStatus.WORKER:
        for job in db_jobs:
            if job.worker_id == current_user.id and (
                job.status == s.JobStatus.PAYMENT_CONFIRMED.value or job.status == s.JobStatus.CANCELED.value
            ):
                job_location, job_address = format_location_string(job.location, job.address, lang)

                jobs_out.append(
                    s.JobByStatus(
                        uuid=job.uuid,
                        title=job.title,
                        location=job_location,
                        address=job_address,
                        start_date=job.start_date,
                        end_date=job.end_date,
                        cost=job.cost,
                        status=s.JobStatus(job.status),
                        required_rate_owner=job.required_rate_owner,
                        required_rate_worker=job.required_rate_worker,
                        files=[s.File.model_validate(file) for file in job.files],
                    )
                )

    return jobs_out
