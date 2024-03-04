import json
import random
from pathlib import Path

import sqlalchemy as sa
from googleapiclient.discovery import Resource, build

from app import models as m
from app import schema as s
from app.database import db
from app.logger import log
from config import BASE_DIR, config

from .utility import SEARCH_IDS, authorized_user_in_google_spreadsheets

CFG = config()


ROOT_PATH = Path(BASE_DIR)
JSON_FILE = ROOT_PATH / "data" / "users.json"


RANGE_NAME = "Users!A1:P"

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


def write_users_in_db(users: list[s.UserFile], with_print: bool = True):
    with db.begin() as session:
        assert session.scalar(
            sa.select(m.Location)
        ), "Locations table is empty. Please run `flask export-regions` first"
        assert session.scalar(sa.select(m.Service)), "Services table is empty. Please run `flask export-services` first"

        for user in users:
            if session.scalar(sa.select(m.User).where(m.User.email == user.email)):
                log(log.DEBUG, "User with email [%s] already exists", user.email)
                continue

            new_user: m.User = m.User(
                fullname=user.fullname,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=user.phone,
                email=user.email,
                password=user.password,
                is_volunteer=user.is_volunteer,
                phone_verified=True,
            )

            for location_id in user.location_ids:
                location = session.scalar(sa.select(m.Location).where(m.Location.id == location_id))
                assert location, f"Location with id [{location_id}] not found"
                new_user.locations.append(location)

            for service_id in user.service_ids:
                service = session.scalar(sa.select(m.Service).where(m.Service.id == service_id))
                assert service, f"Service with id [{service_id}] not found"
                new_user.services.append(service)

            session.add(new_user)
            if with_print:
                log(log.INFO, f"Created user {user.fullname} =====> {user.email} ======> {user.phone}")


# a function for filling the table with phones for users who do not have a phone number. Used only once
def write_phone_to_google_spreadsheets():
    """Write phone to google spreadsheets User"""
    credentials = authorized_user_in_google_spreadsheets()

    OPERATOR_CODE = [50, 63, 66, 67, 68, 73, 99, 44]
    PHONE_RANGE = "Users!O2:O"

    resource: Resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values of column phone
    res: Resource = sheets.values()
    range_ = res.get(spreadsheetId=CFG.SPREADSHEET_ID, range=PHONE_RANGE).execute()
    values = range_["values"]

    generated_values = []
    for val in values:
        if not val or not val[0].strip():
            # generate phone
            while True:
                phone = f"380{random.choice(OPERATOR_CODE)}{random.randint(1000000, 9999999)}"
                if phone not in generated_values:
                    generated_values += [phone]
                    break
            if not val:
                val.append(phone)
            else:
                val[0] = phone
        else:
            val[0] = val[0].strip().replace("(", "").replace(")", "").replace("-", "")
            if len(val[0]) == 10:
                val[0] = f"38{val[0]}"
            elif len(val[0]) == 9:
                val[0] = f"380{val[0]}"

    body = {"values": values}

    result = (
        sheets.values()
        .update(
            spreadsheetId=CFG.SPREADSHEET_ID,
            range=PHONE_RANGE,
            valueInputOption="USER_ENTERED",
            body=body,
        )
        .execute()
    )
    log(log.INFO, "Result: %s", result)


# a function for filling the table with emails for users who do not have an email. Used only once
def write_email_to_google_spreadsheets():
    """Write email to google spreadsheets User"""
    credentials = authorized_user_in_google_spreadsheets()

    EMAIL_PROVIDERS = ["@gmail.com", "@ukr.net", "@i.ua", "@meta.ua", "@bigmir.net"]
    EMAIL_RANGE = "Users!N2:N"

    resource: Resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values of column phone
    res: Resource = sheets.values()
    range_ = res.get(spreadsheetId=CFG.SPREADSHEET_ID, range=EMAIL_RANGE).execute()
    values = range_["values"]

    generated_values = []
    for i, val in enumerate(values):
        if not val or not val[0].strip():
            # generate email
            while True:
                email = f"{i+1}.{EMAIL_PROVIDERS[random.randint(0, len(EMAIL_PROVIDERS) - 1)]}"
                if email not in generated_values:
                    generated_values += [email]
                    break
            if not val:
                val.append(email)
            else:
                val[0] = email

    body = {"values": values}

    result = (
        sheets.values()
        .update(
            spreadsheetId=CFG.SPREADSHEET_ID,
            range=EMAIL_RANGE,
            valueInputOption="USER_ENTERED",
            body=body,
        )
        .execute()
    )
    log(log.INFO, "Result: %s", result)


def export_users_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill users with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()

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

        fullname = row[PERSON_INDEX]
        assert fullname, f"Fullname is empty id: {id}"

        user_services = row[SERVICES_TYPE_INDEX]
        services_ids = [int(i) for i in SEARCH_IDS.findall(user_services)]

        user_regions = row[REGION_INDEX]
        regions_ids = [int(i) for i in SEARCH_IDS.findall(user_regions)]

        email = row[EMAIL_INDEX]
        assert email, f"Email is empty id: {id}"

        users.append(
            s.UserFile(
                fullname=fullname,
                phone="+" + phone,
                email=email,
                first_name=row[FIRST_NAME_INDEX],
                last_name=row[LAST_NAME_INDEX],
                location_ids=regions_ids,
                service_ids=services_ids,
                is_volunteer=False,
                password=USER_PASSWORD,
            )
        )

    if in_json:
        with open(JSON_FILE, "w") as file:
            json.dump(s.UsersFile(users=users).dict(), file, ensure_ascii=False, indent=4)
        return

    write_users_in_db(users, with_print)


def export_users_from_json_file(with_print: bool = True):
    """Fill users with data from json file"""

    with open(JSON_FILE, "r") as file:
        file_data: s.UsersFile = s.UsersFile.model_validate(json.load(file))

    users = file_data.users
    write_users_in_db(users, with_print)
