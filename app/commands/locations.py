import json
from pathlib import Path

import sqlalchemy as sa

from app import models as m
from app import schema as s
from app.database import db
from app.logger import log

MODULE_PATH = Path(__file__).parent
JSON_FILE = MODULE_PATH / ".." / ".." / "data" / "regions.json"
JSON_FILE_LOCATIONS = MODULE_PATH / ".." / ".." / "data" / "locations.json"


def check_if_region_exists(region: s.Region, session: sa.orm.Session):
    """Check if region exists in db"""
    stmt = sa.select(m.Region).where(m.Region.name_ua == region.name_ua)
    db_region = session.scalar(stmt)
    return db_region is not None


def check_if_location_exists(location: s.LocationOut, session: sa.orm.Session):
    """Check if location exists in db"""
    stmt = sa.select(m.Location).where(m.Location.id == location.id)
    db_location = session.scalar(stmt)
    return db_location is not None


def export_regions_from_json_file(with_print: bool = True):
    """Fill regions with data from json file"""

    with open(JSON_FILE, "r") as file:
        file_data = s.RegionsFile.model_validate(json.load(file))

    regions = file_data.regions
    with db.begin() as session:
        for region in regions:
            if check_if_region_exists(region, session):
                continue

            region_db = m.Region(
                name_ua=region.name_ua,
                name_en=region.name_en,
                location=m.Location(),
            )
            if region.svg:
                region_db.svg_value = region.svg

            session.add(region_db)
            session.flush()
            if with_print:
                log(log.DEBUG, f"{region_db.id}: {region_db.name_ua}")

    return


def export_test_locations_from_json_file(with_print: bool = True):
    """Creates records in city table from json"""

    with open(JSON_FILE_LOCATIONS, "r") as file:
        file_data_locations = s.LocationsFile.model_validate(json.load(file))

    locations = file_data_locations.locations
    with db.begin() as session:
        for location in locations:
            if check_if_location_exists(location, session):
                continue

            location_db = m.Location(
                id=location.id,
                uuid=location.uuid,
            )

            session.add(location_db)
            session.flush()
            if with_print:
                log(log.DEBUG, f"{location_db.id}: {location_db.uuid}")

    return
