import json
from pathlib import Path

import sqlalchemy as sa

from app import models as m
from app import schema as s
from app.database import db
from app.logger import log

MODULE_PATH = Path(__file__).parent
JSON_FILE_CITIES = MODULE_PATH / ".." / ".." / "data" / "cities.json"


def check_if_city_exists(city: s.City, session: sa.orm.Session):
    """Check if city exists in db"""

    stmt = sa.select(m.Settlement).where(m.Settlement.district_id == city.district_id)
    db_city = session.scalar(stmt)
    return db_city is not None


def export_cities_from_json_file(with_print: bool = True):
    """Creates records in city table from json"""

    with open(JSON_FILE_CITIES, "r") as file:
        file_data_cities = s.CitiesFile.model_validate(json.load(file))

    cities = file_data_cities.cities
    with db.begin() as session:
        for city in cities:
            if check_if_city_exists(city, session):
                continue

            city_db = m.Settlement(
                location_id=city.location_id,
                district_id=city.district_id,
                city_id=city.city_id,
                kt=city.kt,
                type=s.SettlementType.CITY.name,
                name_ua=city.name_ua,
                name_en=city.name_en,
            )

            session.add(city_db)
            session.flush()
            if with_print:
                log(log.DEBUG, f"{city_db.id}: {city_db.name_ua}")

    return
