from datetime import datetime
from typing import Annotated, Any, List, Union

import sqlalchemy as sa
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status, UploadFile
from sqlalchemy.orm import Session
from mypy_boto3_s3 import S3Client

import api.controllers as c

from api.utils import get_file_extension
import app.models as m
import app.schema as s
from api.dependency import get_current_user, get_s3_connect
from app.database import get_db
from app.logger import log
from app.schema.language import Language
from config import config

CFG = config()

job_router = APIRouter(prefix="/jobs", tags=["jobs"])


@job_router.get(
    "/{job_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=s.JobInfo,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Job not found"},
        status.HTTP_403_FORBIDDEN: {"description": "User does not own job"},
    },
    dependencies=[Depends(get_current_user)],
)
def get_job(
    job_uuid: str,
    lang: Language = Language.UA,
    db: Session = Depends(get_db),
):
    job: m.Job | None = db.scalar(sa.select(m.Job).where(m.Job.uuid == job_uuid))
    if not job:
        log(log.ERROR, "Job [%s] not found", job_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    job_owner = db.scalar(sa.select(m.User).where(m.User.id == job.owner_id))
    if not job_owner:
        log(log.ERROR, "Owner [%s] not found", job.owner_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")

    return c.get_job(job, lang, db, job_owner)


@job_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=s.JobsOut,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Jobs not found"}},
)
def get_jobs(
    query: str = Query(default="", max_length=128),
    lang: Language = Language.UA,
    selected_locations: Annotated[Union[List[str], None], Query()] = None,
    order_by: s.JobsOrderBy = s.JobsOrderBy.CREATED_AT,
    ascending: bool = True,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get jobs by query params"""

    db_jobs = (
        sa.select(m.Job)
        .where(
            m.Job.is_deleted.is_(False),
            m.Job.status == s.JobStatus.PENDING.value,
            m.Job.is_public.is_(True),
            m.Job.worker_id.is_(None),
            m.Job.owner_id != current_user.id,
        )
        .order_by(m.Job.updated_at.desc())
    )

    current_user_applications = db.scalars(
        sa.select(m.Application).where(
            m.Application.is_deleted.is_(False),
            m.Application.worker_id == current_user.id,
        )
    ).all()

    applications_ids = [app.job_id for app in current_user_applications]

    # exclude jobs where user already applied
    if applications_ids:
        db_jobs = db_jobs.where(~m.Job.id.in_(applications_ids))

    if selected_locations or current_user.locations:
        db_jobs = c.filter_jobs_by_locations(selected_locations, db, current_user, db_jobs)

    jobs = c.filter_and_order_jobs(query, lang, db, current_user, db_jobs, order_by)

    if not jobs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jobs not found")

    if not ascending:
        jobs = jobs[::-1]

    jobs_out = c.create_out_search_jobs(jobs, lang, current_user)

    return s.JobsOut(items=jobs_out)


@job_router.get(
    "/jobs-by-status/",
    status_code=status.HTTP_200_OK,
    response_model=s.JobsByStatusList,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Jobs not found"}},
)
def get_jobs_by_status(
    job_status: s.JobStatus = s.JobStatus.PENDING,
    job_user_status: s.JobUserStatus = s.JobUserStatus.OWNER,
    lang: Language = Language.UA,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Get jobs by status"""
    # TODO: add search by query

    db_jobs = db.scalars(
        sa.select(m.Job)
        .where(
            m.Job.is_deleted.is_(False),
        )
        .order_by(m.Job.updated_at.desc())
    ).all()

    if not db_jobs:
        log(log.ERROR, "Jobs not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jobs not found")

    jobs_out: list[s.JobByStatus] = []

    if job_status == s.JobStatus.PENDING:
        jobs_out = c.get_pending_jobs(db_jobs, current_user, job_user_status, lang, db)

    # get active jobs (in progress, approved and on confirmation)
    if job_status == s.JobStatus.IN_PROGRESS:
        active_jobs = db.scalars(
            sa.select(m.Job)
            .where(
                m.Job.is_deleted.is_(False),
                m.Job.status.in_(
                    [s.JobStatus.IN_PROGRESS.value, s.JobStatus.APPROVED.value, s.JobStatus.ON_CONFIRMATION.value]
                ),
            )
            .order_by(m.Job.updated_at.desc())
        ).all()
        jobs_out = c.get_in_progress_jobs(active_jobs, current_user, job_user_status, lang)

    # get archive jobs (completed and canceled)
    if job_status == s.JobStatus.COMPLETED:
        jobs_out = c.get_archived_jobs(db_jobs, current_user, job_user_status, lang)

    return s.JobsByStatusList(items=jobs_out)


@job_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.JobOut,
    responses={
        status.HTTP_409_CONFLICT: {"description": "Selected service not found"},
        status.HTTP_404_NOT_FOUND: {"description": "Selected file not found"},
    },
)
def create_job(
    job: s.JobIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    # user create job
    """Creates new job"""

    service = db.scalar(sa.select(m.Service).where(m.Service.uuid == job.service_uuid))

    if not service:
        log(log.ERROR, "Service [%s] not found", job.service_uuid)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Selected service not found")

    new_job: m.Job = m.Job(
        **job.model_dump(
            exclude={
                "lang",
                "service_uuid",
                "settlement_uuid",
                "address_uuid",
                "start_date",
                "end_date",
                "file_uuids",
            }
        ),
        owner_id=current_user.id,
        start_date=datetime.fromisoformat(job.start_date) if job.start_date else datetime.now(),
        end_date=datetime.fromisoformat(job.end_date) if job.end_date else None,
    )

    db.add(new_job)
    db.commit()

    if job.settlement_uuid:
        location = db.scalar(sa.select(m.Settlement).where(m.Settlement.city_id == job.settlement_uuid))
        if not location:
            log(log.ERROR, "Settlement [%s] not found", job.settlement_uuid)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Selected location not found")

        new_job.location_id = location.location_id
        log(log.INFO, "Settlement [%s] was added to job [%s]", location.id, new_job.id)

    if job.address_uuid:
        address = db.scalar(sa.select(m.Address).where(m.Address.street_id == job.address_uuid))
        if not address:
            log(log.ERROR, "Address [%s] not found", job.address_uuid)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Selected address not found")

        new_job.address_id = address.id
        log(log.INFO, "Address [%s] was added to job [%s]", address.id, new_job.id)

    new_job_service = m.JobService(job_id=new_job.id, service_id=service.id)
    db.add_all([new_job_service, new_job])
    db.commit()
    db.refresh(new_job)
    log(log.INFO, "Service [%s] was added to job [%s]", service.id, new_job.id)

    files: list[s.FileOut] = []

    # check if all files exist in db
    db_files = db.scalars(sa.select(m.File).where(m.File.uuid.in_(job.file_uuids))).all()

    if len(db_files) != len(job.file_uuids):
        log(log.ERROR, "Not all files found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Selected file not found")

    for file in db_files:
        new_job.files.append(file)
        db.commit()
        files.append(file)
        log(log.INFO, "File [%s] was added to job [%s]", file.id, new_job.id)

    db.refresh(new_job)

    job_out = s.BaseJob.model_validate(new_job)

    log(log.INFO, "Job [%s] was created", new_job.id)
    background_tasks.add_task(c.send_created_job_notification, db, new_job)

    return s.JobOut(
        **job_out.model_dump(),
        files=[s.FileOut.model_validate(file) for file in files],
        service=s.Service(
            name=service.name_ua if job.lang == CFG.UA else service.name_en,
            uuid=service.uuid,
        ),
    )


# save file when user create job
@job_router.post(
    "/files",
    status_code=status.HTTP_201_CREATED,
    response_model=list[str],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Unknown file extension"},
    },
    dependencies=[Depends(get_current_user)],
)
def upload_job_file(
    files: list[UploadFile],
    db: Session = Depends(get_db),
    s3_client: S3Client = Depends(get_s3_connect),
):
    """Uploads file for new job"""

    files_out: list[s.FileOut] = []

    for file in files:
        extension = get_file_extension(file)

        file_type = c.get_file_type(extension)

        if file_type == s.FileType.UNKNOWN:
            log(log.ERROR, "Unknown file extension [%s]", extension)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown file extension")

        file_model = c.create_file(
            file=file,
            db=db,
            s3_client=s3_client,
            extension=extension,
            file_type=file_type,
            file_name_url="jobs/files",
        )

        log(log.INFO, "File [%s] was uploaded", file_model.uuid)

        files_out.append(s.FileOut.model_validate(file_model))

    return [file.uuid for file in files_out]


# deleted file
@job_router.delete(
    "/file/{file_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "File not found"},
    },
    dependencies=[Depends(get_current_user)],
)
def delete_job_file(
    file_uuid: str,
    db: Session = Depends(get_db),
    s3_client: S3Client = Depends(get_s3_connect),
):
    """Deletes file for new job"""

    file: m.File | None = db.scalar(sa.select(m.File).where(m.File.uuid == file_uuid))

    if not file:
        log(log.ERROR, "File [%s] not found", file_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    # delete file from s3 because new job was not created yet
    s3_client.delete_object(Bucket=CFG.AWS_S3_BUCKET_NAME, Key=file.key)

    db.delete(file)
    db.commit()

    log(log.INFO, "File was deleted")


@job_router.put(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    response_model=s.JobOut,
)
def put_job(
    job_id: int,
    job_data: s.JobPut,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    job: m.Job | None = db.scalar(sa.select(m.Job).where(m.Job.id == job_id))
    if not job:
        log(log.ERROR, "Job [%s] not found", job_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.owner_id != current_user.id:
        log(log.ERROR, "User [%s] does not own job [%s]", current_user.id, job_id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not own job")

    data_filtered: dict[str, Any] = {key: value for key, value in job_data.model_dump().items() if value is not None}

    db.execute(sa.update(m.Job).where(m.Job.id == job_id).values(**data_filtered))
    db.commit()
    log(log.INFO, "Updated job [%s]", job_id)
    return job


@job_router.post("/search", status_code=status.HTTP_200_OK, response_model=s.JobsSearchOut)
def search_jobs(
    query: s.JobSearchIn,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    responses={
        status.HTTP_409_CONFLICT: {"description": "Selected service not found"},
    },
):
    """Returns filtered list of jobs"""
    return c.search_jobs(query, current_user, db)


@job_router.post("/home", status_code=status.HTTP_200_OK, response_model=s.JobsCardList)
def get_jobs_on_home_page(
    query: s.JobHomePage,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Returns jobs for home page"""
    return c.get_jobs_on_home_page(query, current_user, db)


@job_router.get("/public-job-statistics/", status_code=status.HTTP_200_OK, response_model=s.PublicJobDict)
def get_public_job_statistics(
    db: Session = Depends(get_db),
):
    """Get statistics for jobs per location"""

    return c.job_statistics(db)


@job_router.delete(
    "/{job_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Job not found"}},
)
def delete_job(
    job_uuid: str,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    job: m.Job | None = db.scalar(sa.select(m.Job).where(m.Job.uuid == job_uuid))

    if not job:
        log(log.ERROR, "Job [%s] not found", job_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.owner_id != current_user.id:
        log(log.ERROR, "User [%s] does not own job [%s]", current_user.id, job.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not own job")

    job.is_deleted = True
    db.commit()

    log(log.INFO, "Job [%s] was deleted", job.id)


@job_router.put(
    "/{job_uuid}/status",
    status_code=status.HTTP_200_OK,
    response_model=s.JobStatusIn,
)
def put_job_status(
    job_uuid: str,
    job_data: s.JobStatusIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    job: m.Job | None = db.scalar(sa.select(m.Job).where(m.Job.uuid == job_uuid))
    if not job:
        log(log.ERROR, "Job [%s] not found", job_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job_data.status == s.JobStatus.PENDING:
        log(log.ERROR, "[put_job_status] Job [%s] status downgrade to pending is forbidden", job_uuid)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job status downgrade forbidden")

    if job_data.status == s.JobStatus.APPROVED:
        log(log.ERROR, "[put_job_status] Job [%s] status downgrade to approved is forbidden", job_uuid)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job status downgrade forbidden")

    if job_data.status == s.JobStatus.IN_PROGRESS and job.status == s.JobStatus.APPROVED.value:
        if current_user.id != job.worker_id:
            log(
                log.ERROR,
                "[put_job_status] User is not a worker for job [%s]. Setting status to in progress forbidden",
                job_uuid,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=" User is not a worker for this job. Setting status to in progress forbidden",
            )

        job.status = s.JobStatus.IN_PROGRESS.value
        log(log.INFO, "Updated job [%s] status to IN_PROGRESS", job_uuid)
        db.commit()
        return job

    if job_data.status == s.JobStatus.ON_CONFIRMATION and job.status == s.JobStatus.IN_PROGRESS.value:
        if current_user.id != job.worker_id:
            log(
                log.ERROR,
                "[put_job_status] User is not an worker for job [%s]. Setting status to on confirmation forbidden",
                job_uuid,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is not an worker for this job. Setting status to on confirmation forbidden",
            )

        job.status = s.JobStatus.ON_CONFIRMATION.value
        log(log.INFO, "Updated job [%s] status to ON_CONFIRMATION", job_uuid)

        db.commit()
        return job

    if job_data.status == s.JobStatus.COMPLETED and job.status == s.JobStatus.ON_CONFIRMATION.value:
        if current_user.id != job.owner_id:
            log(
                log.ERROR,
                "[put_job_status] User is not an owner for job [%s]. Setting status to completed forbidden",
                job_uuid,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is not an owner for this job. Setting status to completed forbidden",
            )

        job.status = s.JobStatus.COMPLETED.value
        log(log.INFO, "Updated job [%s] status to COMPLETED", job_uuid)

        db.commit()
        return job

    if job_data.status == s.JobStatus.CANCELED:
        if current_user.id != job.owner_id:
            log(
                log.ERROR,
                "[put_job_status] User is not an owner for job [%s]. Setting status to canceled forbidden",
                job_uuid,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is not an owner for this job. Setting status to canceled forbidden",
            )

        job.status = s.JobStatus.CANCELED.value
        log(log.INFO, "Updated job [%s] status to CANCELED", job_uuid)

        db.commit()
        return job

    log(
        log.ERROR,
        "Updated job [%s] status. Status mismatch, current [%s], new: [%s]",
        job_uuid,
        job.status,
        job_data.status,
    )
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Status mismatch")
