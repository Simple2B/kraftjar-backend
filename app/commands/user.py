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
from config import config

CFG = config()


MODULE_PATH = Path(__file__).parent
JSON_FILE = MODULE_PATH / ".." / ".." / "data" / "users.json"


SCOPES = CFG.SCOPES
SPREADSHEET_ID = CFG.SPREADSHEET_ID

RANGE_NAME = "Users!A1:P"
# rows name
# ['id', 'Персонаж', 'Статус', 'Вид послуг', 'Область', 'Стать', 'Вік', 'Рейтинг', 'З нами вже', 'Робіт/замовлень', 'Опис', 'Імʼя', 'Прізвище', 'e-mail', 'phone', 'id']
PERSON = "Персонаж"
SERVICES_TYPE = "Вид послуг"
REGION = "Область"
NAME = "Імʼя"
SURNAME = "Прізвище"
EMAIL = "e-mail"
PHONE = "phone"

TOKEN_FILE = MODULE_PATH / "token.json"


def export_users_from_google_spreadsheets(with_print: bool = True):
    """Fill users with data from google spreadsheets"""

    credentials = None
    # auth process - > create token.json
    if Path.exists(TOKEN_FILE):
        credentials = Credentials.from_authorized_user("token.json", SCOPES)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            credentials = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(credentials.to_json())

    try:
        # get data from google spreadsheets
        service = build("sheets", "v4", credentials=credentials)
        sheets = service.spreadsheets()

        # get all values from sheet Users
        result = sheets.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get("values", [])

        if not values:
            log(log.INFO, "No data found")
            return

        # indexes of row values
        PERSON_INDEX = values[0].index(PERSON)
        PHONE_INDEX = values[0].index(PHONE)
        EMAIL_INDEX = values[0].index(EMAIL)
        SERVICES_TYPE_INDEX = values[0].index(SERVICES_TYPE)

        # TODO: first  name and last name must be add to model User
        NAME_INDEX = values[0].index(NAME)
        # SURNAME_INDEX = values[0].index(SURNAME)

        # TODO: correct data region in google sheet
        # REGION_INDEX = values[0].index(REGION)

        with db.begin() as session:
            if not session.scalar(sa.select(m.Location)):
                log(log.ERROR, "Locations table is empty")
                log(log.ERROR, "Please run `flask export-regions` first")
                raise Exception("Locations table is empty. Please run `flask export-regions` first")
            if not session.scalar(sa.select(m.Service)):
                log(log.ERROR, "Services table is empty")
                log(log.ERROR, "Please run `flask export-services` first")
                raise Exception("Services table is empty. Please run `flask export-services` first")

            for row in values:
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
                user_firstname = row[NAME_INDEX]
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
                services_ids = re.findall(r"\d+", user_services)

                for service_id in services_ids:
                    service: m.Service | None = session.scalar(sa.select(m.Service).where(m.Service.id == service_id))
                    if not service:
                        log(log.ERROR, "Service with id [%s] not found", service_id)
                        raise Exception(f"Service with id [{service_id}] not found")
                    new_user.services.append(service)

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
