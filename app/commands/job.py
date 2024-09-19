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
START_DATE = "start_date"
END_DATE = "end_date"
RATE_OWNER = "rate_client"
RATE_WORKER = "rate_worker"
COST = "cost"
STATUS = "status"

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

        if not session.scalar(sa.select(m.Address)):
            log(log.ERROR, "Address table is empty")
            log(log.ERROR, "Please run `flask export-addresses` first")
            raise Exception("Address table is empty. Please run `flask export-addresses` first")

        for job in jobs:
            new_job: m.Job = m.Job(
                title=job.title,
                description=job.description,
                address_id=job.address_id,
                location_id=job.location_id,
                # time=job.time,
                status=job.status.value,
                is_public=job.is_public,
                owner_id=job.owner_id,
                worker_id=job.worker_id,
                created_at=job.created_at,
                updated_at=job.updated_at,
                is_deleted=job.is_deleted,
                start_date=job.start_date,
                end_date=job.end_date,
                cost=job.cost,
            )

            db_services: list[m.Service] = session.scalars(
                sa.select(m.Service).where(m.Service.id.in_(job.services))
            ).all()
            assert db_services, "Services not found"

            session.add(new_job)
            session.flush()

            for service in db_services:
                new_job_service: m.JobService = m.JobService(
                    service_id=service.id,
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
    RANGE_NAME = "Contacts!A1:O"

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
    ADDRESS_INDEX = values[0].index(ADDRESS)
    CREATED_AT_INDEX = values[0].index(CREATED_AT)
    START_DATE_INDEX = values[0].index(START_DATE)
    END_DATE_INDEX = values[0].index(END_DATE)
    RATE_OWNER_INDEX = values[0].index(RATE_OWNER)
    RATE_WORKER_INDEX = values[0].index(RATE_WORKER)
    STATUS_INDEX = values[0].index(STATUS)
    COST_INDEX = values[0].index(COST)

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
        services_ids = SEARCH_IDS.findall(job_service)
        assert services_ids, f"The service {services_ids} is empty"

        job_location = row[LOCATION_INDEX]
        location_ids = SEARCH_IDS.findall(job_location)

        if location_ids:
            location_id = int(location_ids[0])
        else:
            location_id = None

        job_address = row[ADDRESS_INDEX]
        address_ids = SEARCH_IDS.findall(job_address)

        if address_ids:
            address_id = int(address_ids[0])
        else:
            address_id = None

        created_at = row[CREATED_AT_INDEX]
        assert created_at, f"The created_at {created_at} is empty"

        start_date = row[START_DATE_INDEX]
        assert start_date, f"The started_at {start_date} is empty"

        end_date = row[END_DATE_INDEX]

        rate_owner = row[RATE_OWNER_INDEX]
        assert rate_owner, f"The rate_owner {rate_owner} is empty"
        rate_worker = row[RATE_WORKER_INDEX]
        assert rate_worker, f"The rate_worker {rate_worker} is empty"

        cost = row[COST_INDEX]
        assert cost, f"The cost {cost} is empty"

        status = row[STATUS_INDEX]
        assert status, f"The status {status} is empty"

        jobs.append(
            s.JobCompletedCreate(
                title=title,
                description=description,
                address_id=address_id,
                location_id=location_id,
                # time="",
                status=status,
                is_public=True,
                owner_id=owner_id,
                worker_id=worker_id,
                created_at=datetime.strptime(TEST_DATA, "%d.%m.%Y"),
                updated_at=datetime.strptime(TEST_DATA, "%d.%m.%Y"),
                is_deleted=False,
                rate_owner=rate_owner,
                rate_worker=rate_worker,
                start_date=datetime.strptime(start_date, "%d.%m.%Y"),
                end_date=datetime.strptime(end_date, "%d.%m.%Y") if end_date else None,
                cost=cost,
                services=services_ids,
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
