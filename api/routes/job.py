from datetime import datetime
from typing import Annotated, Sequence, cast, Any

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile
from sqlalchemy.orm import Session
from mypy_boto3_s3 import S3Client

import api.controllers as c

from api.utils import get_file_extension
import app.models as m
import app.schema as s
from api.dependency import get_current_user, get_user, get_s3_connect
from app.database import get_db
from app.logger import log
from app.schema.language import Language
from config import config

CFG = config()

job_router = APIRouter(prefix="/jobs", tags=["jobs"])


@job_router.get("/{job_id}", status_code=status.HTTP_200_OK, response_model=s.JobOut)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: m.User | None = Depends(get_user),
):
    job: m.Job | None = db.scalar(sa.select(m.Job).where(m.Job.id == job_id))
    if not job:
        log(log.ERROR, "Job [%s] not found", job_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@job_router.get("/", status_code=status.HTTP_200_OK, response_model=s.JobOutList)
def get_jobs(
    db: Session = Depends(get_db),
    # get cur_user
    current_user: m.User | None = Depends(get_user),
):
    query = sa.select(m.Job)
    if current_user:
        query = query.where(m.Job.user_id == current_user.id)
    jobs: Sequence[m.Job] = db.scalars(query).all()
    return s.JobOutList(jobs=cast(list, jobs))


@job_router.get(
    "/all/",
    status_code=status.HTTP_200_OK,
    response_model=s.JobsOut,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Jobs not found"}},
)
def get_jobs_all(
    query: str = Query(default="", max_length=128),
    lang: Language = Language.UA,
    selected_locations: Annotated[list[str] | None, Query()] = None,
    order_by: s.JobsOrderBy = s.JobsOrderBy.START_DATE,
    ascending: bool = True,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get jobs by query params"""

    db_jobs = sa.select(m.Job).where(
        m.Job.is_deleted.is_(False),
        m.Job.status == s.JobStatus.PENDING,
        m.Job.is_public.is_(True),
        m.Job.owner_id != current_user.id,
    )

    # TODO: All Ukraine select
    if selected_locations or current_user.locations:
        db_jobs = c.filter_jobs_by_locations(selected_locations, db, current_user, db_jobs)

    jobs = c.filter_and_order_jobs(query, lang, db, current_user, db_jobs, order_by)

    if not jobs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jobs not found")

    if not ascending:
        jobs = jobs[::-1]

    jobs_out = c.create_out_search_jobs(jobs, lang, db)

    return s.JobsOut(items=jobs_out)


# user create job
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
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
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
                "location_uuid",
                "start_date",
                "end_date",
                "file_uuids",
            }
        ),
        owner_id=current_user.id,
        start_date=datetime.fromisoformat(job.start_date) if job.start_date else None,
        end_date=datetime.fromisoformat(job.end_date) if job.end_date else None,
    )

    db.add(new_job)
    db.commit()

    if job.location_uuid:
        location = db.scalar(sa.select(m.Location).where(m.Location.uuid == job.location_uuid))
        if not location:
            log(log.ERROR, "Location [%s] not found", job.location_uuid)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Selected location not found")

        new_job.location_id = location.id
        log(log.INFO, "Location [%s] was added to job [%s]", location.id, new_job.id)

    m.JobService(job_id=new_job.id, service_id=service.id)
    db.add(new_job)
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
        m.JobFile(job_id=new_job.id, file_id=file.id)
        db.add(new_job)
        files.append(file)
        log(log.INFO, "File [%s] was added to job [%s]", file.id, new_job.id)

    db.commit()
    db.refresh(new_job)

    job_out = s.BaseJob.model_validate(new_job)

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


@job_router.put("/{job_id}", status_code=status.HTTP_200_OK, response_model=s.JobOut)
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
