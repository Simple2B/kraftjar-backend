import re
import random
import json
from pathlib import Path

import sqlalchemy as sa

from app import models as m
from app import schema as s
from app.database import db
from app.logger import log

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import config, BASE_DIR

CFG = config()


ROOT_PATH = Path(BASE_DIR)
JSON_FILE = ROOT_PATH / "data" / "users.json"


RANGE_NAME = "Users!A1:P"
# rows name
# ['id', 'Персонаж', 'Статус', 'Вид послуг', 'Область', 'Стать', 'Вік', 'Рейтинг', 'З нами вже', 'Робіт/замовлень', 'Опис', 'Імʼя', 'Прізвище', 'e-mail', 'phone', 'id']
PERSON = "Персонаж"
SERVICES_TYPE = "Вид послуг"
REGION = "Область"
FIRST_NAME = "Імʼя"
LAST_NAME = "Прізвище"
EMAIL = "e-mail"
PHONE = "phone"

ALL_REGIONS = "Вся Україна"

TOKEN_FILE = ROOT_PATH / "token.json"
USER_PASSWORD = "Kraftjar2024"
SEARCH_SERVICE_IDS = re.compile(r"\((?P<id>\d+)\)")


def write_phone_to_google_spreadsheets():
    pass


def export_users_from_google_spreadsheets(with_print: bool = True):
    """Fill users with data from google spreadsheets"""

    credentials = None
    # auth process - > create token.json
    if Path.exists(TOKEN_FILE):
        credentials = Credentials.from_authorized_user_file(TOKEN_FILE, CFG.SCOPES)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", CFG.SCOPES)
            credentials = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(credentials.to_json())

    try:
        # get data from google spreadsheets
        resource = build("sheets", "v4", credentials=credentials)
        sheets = resource.spreadsheets()

        # get all values from sheet Users
        result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get("values", [])

        assert values, "No data found"

        users: list[s.UserFile] = []

        # indexes of row values
        INDEX_ID = values[0].index("id")
        PERSON_INDEX = values[0].index(PERSON)
        PHONE_INDEX = values[0].index(PHONE)
        EMAIL_INDEX = values[0].index(EMAIL)
        SERVICES_TYPE_INDEX = values[0].index(SERVICES_TYPE)
        FIRST_NAME_INDEX = values[0].index(FIRST_NAME)
        LAST_NAME_INDEX = values[0].index(LAST_NAME)
        REGION_INDEX = values[0].index(REGION)

        for row in values[1:]:
            id = row[INDEX_ID]
            phone = row[PHONE_INDEX]

            assert phone, f"Phone is empty id: {id}"
            user_services = row[SERVICES_TYPE_INDEX]
            services_ids = [int(i) for i in SEARCH_SERVICE_IDS.findall(user_services)]

            user_regions = row[REGION_INDEX]
            regions_ids = [int(i) for i in SEARCH_SERVICE_IDS.findall(user_regions)]

            if ALL_REGIONS in regions_ids:
                regions_ids = [db_region.id for db_region in db.scalars(sa.select(m.Region)).all()]
            users.append(
                s.UserFile(
                    fullname=row[PERSON_INDEX],
                    phone=phone,
                    email=row[EMAIL_INDEX],
                    first_name=row[FIRST_NAME_INDEX],
                    last_name=row[LAST_NAME_INDEX],
                    location_ids=regions_ids,
                    service_ids=services_ids,
                    is_volunteer=False,
                    password=USER_PASSWORD,
                )
            )

        with db.begin() as session:
            assert session.scalar(
                sa.select(m.Location)
            ), "Locations table is empty. Please run `flask export-regions` first"
            assert session.scalar(
                sa.select(m.Service)
            ), "Services table is empty. Please run `flask export-services` first"

            for row in values[1:]:
                user_fullname = row[PERSON_INDEX]
                if not user_fullname:
                    log(log.INFO, "This row is empty")
                    continue
                user_phone: str = ""
                # TODO: change this code
                if not row[PHONE_INDEX]:
                    code = random.randint(63, 99)
                    num = random.randint(100, 999)
                    user_phone = f"380{code}1234{num}"
                else:
                    user_phone = row[PHONE_INDEX]

                if session.scalar(sa.select(m.User).where(m.User.phone == user_phone)):
                    log(log.INFO, "User with phone [%s] already exists", user_phone)
                    continue

                # TODO: add to model User firstname and lastname
                user_firstname = row[FIRST_NAME_INDEX]
                # user_lastname = row[SURNAME_INDEX]

                user_email: str = row[EMAIL_INDEX]
                if not user_email:
                    user_email = f"{user_firstname.lower().strip()}@gmail.com"
                user_password = "123"

                new_user: m.User = m.User(
                    fullname=user_fullname,
                    phone=user_phone,
                    email=user_email,
                    password=user_password,
                    phone_verified=True,
                )

                # TODO: must be add location
                # location_id =
                # location: m.Location | None = session.scalar(
                #     sa.select(m.Location).where(m.Location.id == location_id)
                # )
                # if not location:
                #     log(log.ERROR, "Location with id [%s] not found", location_id)
                #     raise Exception(f"Location with id [{location_id}] not found")
                # new_user.locations.append(location)

                user_services = row[SERVICES_TYPE_INDEX]
                services_ids = [int(i) for i in SEARCH_SERVICE_IDS.findall(user_services)]

                for service_id in services_ids:
                    svc: m.Service | None = session.scalar(sa.select(m.Service).where(m.Service.id == service_id))
                    if not svc:
                        log(log.ERROR, "Service with id [%s] not found", service_id)
                        raise Exception(f"Service with id [{service_id}] not found")
                    new_user.services.append(svc)

                session.add(new_user)
                if with_print:
                    log(log.INFO, f"Created user {new_user.fullname}")

    except HttpError as error:
        log(log.ERROR, "An error occurred: %s", error)
        raise Exception("An error occurred")


def export_users_from_json_file(with_print: bool = True):
    """Fill users with data from json file"""

    with open(JSON_FILE, "r") as file:
        file_data: s.UsersFile = s.UsersFile.model_validate(json.load(file))

    with db.begin() as session:
        if not session.scalar(sa.select(m.Location)):
            log(log.ERROR, "Locations table is empty")
            log(log.ERROR, "Please run `flask export-regions` first")
            raise Exception("Locations table is empty. Please run `flask export-regions` first")

        if not session.scalar(sa.select(m.Service)):
            log(log.ERROR, "Services table is empty")
            log(log.ERROR, "Please run `flask export-services` first")
            raise Exception("Services table is empty. Please run `flask export-services` first")

        for user in file_data.users:
            if session.scalar(sa.select(m.User).where(m.User.phone == user.phone)):
                log(log.INFO, "User with phone [%s] already exists", user.phone)
                continue

            new_user: m.User = m.User(
                fullname=user.fullname,
                phone=user.phone,
                email=user.email,
                password=user.password,
                is_volunteer=user.is_volunteer,
            )

            for location_id in user.location_ids:
                location: m.Location | None = session.scalar(sa.select(m.Location).where(m.Location.id == location_id))
                if not location:
                    log(log.ERROR, "Location with id [%s] not found", location_id)
                    raise Exception(f"Location with id [{location_id}] not found")
                new_user.locations.append(location)

            for service_id in user.service_ids:
                service: m.Service | None = session.scalar(sa.select(m.Service).where(m.Service.id == service_id))
                if not service:
                    log(log.ERROR, "Service with id [%s] not found", service_id)
                    raise Exception(f"Service with id [{service_id}] not found")
                new_user.services.append(service)

            session.add(new_user)
            if with_print:
                log(log.INFO, f"Created user {user.fullname}")
