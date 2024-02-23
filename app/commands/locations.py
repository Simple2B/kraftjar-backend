import json

from pathlib import Path

import sqlalchemy as sa

from app import models as m
from app import schema as s
from app.database import db

MODULE_PATH = Path(__file__).parent
JSON_FILE = MODULE_PATH / ".." / ".." / "data" / "regions.json"


def check_if_region_exists(region: s.Region):
    """Check if region exists in db"""
    with db.begin() as session:
        stmt = sa.select(m.Region).where(m.Region.name_ua == region.name_ua)
        db_region = session.scalar(stmt)
        return db_region is not None


def export_regions_from_json_file(with_print: bool = True):
    """Fill regions with data from json file"""

    with open(JSON_FILE, "r") as file:
        file_data = s.RegionsFile.model_validate(json.load(file))

    regions = file_data.regions
    with db.begin() as session:
        for region in regions:
            if check_if_region_exists(region):
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
                print(f"{region_db.id}: {region_db.name_ua}")

    return
