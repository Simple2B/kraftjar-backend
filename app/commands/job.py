import json
from datetime import datetime

import sqlalchemy as sa
from googleapiclient.discovery import build

from app import models as m
from app import schema as s
from app.database import db
from app.logger import log
from config import config

from .utility import SEARCH_IDS, authorized_user_in_google_spreadsheets
from .rate import fix_users_average_rate

CFG = config()

# ['ID', 'owner_id', 'worker_id', 'title', 'description', 'service', 'location', 'address', 'created_at', 'started_at', 'finished_at', 'rate_owner', 'rate_worker']
ID = "ID"
OWNER_ID = "owner_id"
WORKER_ID = "worker_id"
TITLE = "title"
DESCRIPTION = "description"
SERVICE = "service"
LOCATION = "location"
ADDRESS = "address"
CREATED_AT = "created_at"
STARTED_AT = "started_at"
FINISHED_AT = "finished_at"
RATE_OWNER = "rate_client"
RATE_WORKER = "rate_worker"

# TODO: add logic of create address_id
TEST_ADDRESS_ID = 1
TEST_DATA = "01.11.2023"


def write_jobs_in_db(jobs: list[s.JobCompletedCreate]):
    with db.begin() as session:
        if not session.scalar(sa.select(m.Location)):
            log(log.ERROR, "Locations table is empty")
            log(log.ERROR, "Please run `flask export-regions` first")
            raise Exception("Locations table is empty. Please run `flask export-regions` first")

        if not session.scalar(sa.select(m.Service)):
            log(log.ERROR, "Services table is empty")
            log(log.ERROR, "Please run `flask export-services` first")
            raise Exception("Services table is empty. Please run `flask export-services` first")
        service_id = 1

        for job in jobs:
            db_address: m.Address = session.scalar(sa.select(m.Address).where(m.Address.id == job.address_id))
            assert db_address, f"Service with id [{db_address}] not found"

            new_job: m.Job = m.Job(
                title=job.title,
                description=job.description,
                address_id=job.address_id,
                location_id=job.location_id,
                time=job.time,
                status=job.status,
                is_public=job.is_public,
                owner_id=job.owner_id,
                worker_id=job.worker_id,
                created_at=job.created_at,
                updated_at=job.updated_at,
                is_deleted=job.is_deleted,
            )

            db_service: m.Service = session.scalar(sa.select(m.Service).where(m.Service.id == service_id))
            assert db_service, f"Service with id [{db_service}] not found"

            session.add(new_job)
            session.flush()

            new_job_service: m.JobService = m.JobService(
                service_id=db_service.id,
                job_id=new_job.id,
            )

            session.add(new_job_service)

            rate_worker: m.Rate = m.Rate(
                message="Mocked rate",
                gives_id=new_job.owner_id,
                receiver_id=new_job.worker_id,
                job_id=new_job.id,
                rate=job.rate_worker,
            )
            rate_owner: m.Rate = m.Rate(
                message="Mocked rate",
                gives_id=new_job.worker_id,
                receiver_id=new_job.owner_id,
                job_id=new_job.id,
                rate=job.rate_owner,
            )
            session.add_all([rate_worker, rate_owner])

            log(log.DEBUG, "Job with title [%s] created", job.title)

    fix_users_average_rate()


def export_jobs_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill users with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()
    RANGE_NAME = "Contacts!A1:M"

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"

    jobs: list[s.JobCompletedCreate] = []

    # indexes of row values
    INDEX_ID = values[0].index(ID)
    OWNER_ID_INDEX = values[0].index(OWNER_ID)
    WORKER_ID_INDEX = values[0].index(WORKER_ID)
    TITLE_INDEX = values[0].index(TITLE)
    DESCRIPTION_INDEX = values[0].index(DESCRIPTION)
    SERVICE_INDEX = values[0].index(SERVICE)
    LOCATION_INDEX = values[0].index(LOCATION)
    # ADDRESS_INDEX = values[0].index(ADDRESS)
    CREATED_AT_INDEX = values[0].index(CREATED_AT)
    STARTED_AT_INDEX = values[0].index(STARTED_AT)
    FINISHED_AT_INDEX = values[0].index(FINISHED_AT)
    RATE_OWNER_INDEX = values[0].index(RATE_OWNER)
    RATE_WORKER_INDEX = values[0].index(RATE_WORKER)

    for row in values[1:]:
        if len(row) < 12:
            continue

        if not row[INDEX_ID]:
            continue

        owner_id = row[OWNER_ID_INDEX]
        assert owner_id, f"The owner {owner_id} is missing"

        worker_id = row[WORKER_ID_INDEX]
        assert worker_id, f"The worker {worker_id} is missing"

        title = row[TITLE_INDEX]
        description = row[DESCRIPTION_INDEX]

        if len(description) > 1024:
            description = description[:1024]

        job_service = row[SERVICE_INDEX]
        service = SEARCH_IDS.findall(job_service)
        assert service, f"The service {service} is empty"

        job_location = row[LOCATION_INDEX]
        location_ids = SEARCH_IDS.findall(job_location)

        if location_ids:
            location_id = int(location_ids[0])
        else:
            location_id = None

        created_at = row[CREATED_AT_INDEX]
        assert created_at, f"The created_at {created_at} is empty"

        started_at = row[STARTED_AT_INDEX]
        assert started_at, f"The started_at {started_at} is empty"

        finished_at = row[FINISHED_AT_INDEX]
        assert finished_at, f"The finished_at {finished_at} is empty"

        rate_owner = row[RATE_OWNER_INDEX]
        assert rate_owner, f"The rate_owner {rate_owner} is empty"
        rate_worker = row[RATE_WORKER_INDEX]
        assert rate_worker, f"The rate_worker {rate_worker} is empty"

        jobs.append(
            s.JobCompletedCreate(
                title=title,
                description=description,
                address_id=TEST_ADDRESS_ID,
                location_id=location_id,
                time="",
                status=s.JobStatus.COMPLETED,
                is_public=True,
                owner_id=owner_id,
                worker_id=worker_id,
                created_at=datetime.strptime(TEST_DATA, "%d.%m.%Y"),
                updated_at=datetime.strptime(TEST_DATA, "%d.%m.%Y"),
                is_deleted=False,
                rate_owner=rate_owner,
                rate_worker=rate_worker,
            )
        )

    if in_json:
        with open("data/jobs.json", "w") as file:
            json.dump(s.JobsFile(jobs=jobs).model_dump(mode="json"), file, indent=4)
        return

    write_jobs_in_db(jobs)


def export_jobs_from_json_file(max_job_limit: int | None = None):
    """Fill users with data from json file"""

    with open("data/jobs.json", "r") as file:
        file_data = s.JobsFile.model_validate(json.load(file))

    jobs = file_data.jobs
    if max_job_limit:
        jobs = jobs[:max_job_limit]
    write_jobs_in_db(jobs)
