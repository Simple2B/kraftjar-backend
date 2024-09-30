import json
from pathlib import Path

import sqlalchemy as sa

from app import models as m
from app import schema as s
from app.database import db
from app.logger import log

MODULE_PATH = Path(__file__).parent
JSON_FILE_RAYONS = MODULE_PATH / ".." / ".." / "data" / "rayons.json"


def check_if_rayon_exists(rayon: s.Rayon, session: sa.orm.Session):
    """Check if rayon exists in db"""

    stmt = sa.select(m.Rayon).where(m.Rayon.district_id == rayon.district_id)
    db_rayon = session.scalar(stmt)
    return db_rayon is not None


def export_rayons_from_json_file(with_print: bool = True, write_to_file=False):
    """Creates records in rayon table from json"""

    if write_to_file:
        with db.begin() as session:
            rayons = session.scalars(sa.select(m.Rayon)).all()
            log(log.DEBUG, f"Rayons count: {len(rayons)}")

            with open("data/rayons.json", "w") as file:
                json.dump(s.RayonsList(rayons=rayons).model_dump(mode="json"), file, indent=4)
        return

    with open(JSON_FILE_RAYONS, "r") as file:
        file_data_rayons = s.RayonsList.model_validate(json.load(file))

    rayons = file_data_rayons.rayons
    with db.begin() as session:
        for rayon in rayons:
            if check_if_rayon_exists(rayon, session):
                continue

            rayon_db = m.Rayon(
                location_id=rayon.location_id,
                district_id=rayon.district_id,
                name_ua=rayon.name_ua,
                name_en=rayon.name_en,
            )

            session.add(rayon_db)
            session.flush()
            if with_print:
                log(log.DEBUG, f"{rayon_db.id}: {rayon_db.name_ua}")

    return
