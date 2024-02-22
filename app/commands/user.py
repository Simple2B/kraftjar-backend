import os
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


SCOPES = CFG.SCOPES
SPREADSHEET_ID = CFG.SPREADSHEET_ID


def export_users_from_google_spreadsheets(with_print: bool = True):
    """Fill users with data from google spreadsheets"""

    credentials = None
    # auth process - > create token.json
    if os.path.exists("token.json"):
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

        # get all values from sheet
        # get all values from sheet Users
        # result = sheets.values().get(spreadsheetId=SPREADSHEET_ID, range="Users!A1:O217").execute()
        # values = result.get("values", [])

        with db.begin() as session:
            if not session.scalar(sa.select(m.Location)):
                log(log.ERROR, "Locations table is empty")
                log(log.ERROR, "Please run `flask export-regions` first")
                raise Exception("Locations table is empty. Please run `flask export-regions` first")

            if not session.scalar(sa.select(m.Service)):
                log(log.ERROR, "Services table is empty")
                log(log.ERROR, "Please run `flask export-services` first")
                raise Exception("Services table is empty. Please run `flask export-services` first")

            for row in range(2, 217):
                user_phone: str = sheets.values().get(spreadsheetId=SPREADSHEET_ID, range=f"Users!O{row}").execute()
                if session.scalar(sa.select(m.User).where(m.User.phone == user_phone)):
                    log(log.INFO, "User with phone [%s] already exists", user_phone)
                    continue
                if not user_phone:
                    for num in range(10, 99):
                        user_phone = f"+3809912345{num}"
                user_fullname = sheets.values().get(spreadsheetId=SPREADSHEET_ID, range=f"Users!A{row}").execute()

                user_email = sheets.values().get(spreadsheetId=SPREADSHEET_ID, range=f"Users!N{row}").execute()

                if not user_email:
                    user_email = f"{user_fullname}@mail.com"

                user_password = "#" + user_fullname
                new_user: m.User = m.User(
                    fullname=user_fullname,
                    phone=user_phone,
                    email=user_email,
                    password=user_password,
                    # is_volunteer=user_is_volunteer,
                )

                # TODO: must be add services and location
                # location_id =
                # location: m.Location | None = session.scalar(
                #     sa.select(m.Location).where(m.Location.id == location_id)
                # )
                # if not location:
                #     log(log.ERROR, "Location with id [%s] not found", location_id)
                #     raise Exception(f"Location with id [{location_id}] not found")
                # new_user.locations.append(location)

                # service_id =
                # service: m.Service | None = session.scalar(sa.select(m.Service).where(m.Service.id == service_id))
                # if not service:
                #     log(log.ERROR, "Service with id [%s] not found", service_id)
                #     raise Exception(f"Service with id [{service_id}] not found")
                # new_user.services.append(service)

                session.add(new_user)
                session.refresh(new_user)
                if with_print:
                    log(log.INFO, f"Created user {new_user.fullname}")

    except HttpError as error:
        log(log.ERROR, "An error occurred: %s", error)
        raise Exception("An error occurred")


MODULE_PATH = Path(__file__).parent
JSON_FILE = MODULE_PATH / ".." / ".." / "data" / "users.json"


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
