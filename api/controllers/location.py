from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import Executable

from app import models as m
from app import schema as s
from config import config

CFG = config()


def get_locations(query: s.LocationsIn, db: Session) -> s.LocationsOut:
    """Get locations"""
    stmt: Executable = sa.select(m.Region).where(m.Region.is_deleted == sa.false())
    db_regions: Sequence[m.Region] = db.scalars(stmt).all()
    locations: list[s.Location] = [
        s.Location(
            uuid=region.location.uuid,
            name=region.name_ua if query.lang == CFG.UA else region.name_en,
            svg=region.svg_value,
        )
        for region in db_regions
    ]

    return s.LocationsOut(lang=query.lang, locations=locations, selected=query.selected)
