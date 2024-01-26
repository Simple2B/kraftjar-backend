import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import schema as s
from app import models as m


def get_locations(query: s.LocationsIn, db: Session) -> s.LocationsOut:
    """Get locations"""
    stmt = sa.select(m.Region).where(m.Region.is_deleted == sa.false())
    db_regions = db.scalars(stmt).all()
    if query.lang == "ua":
        locations = [
            s.Location(uuid=region.location.uuid, name=region.name_ua, svg=region.svg_value) for region in db_regions
        ]
    else:
        locations = [
            s.Location(uuid=region.location.uuid, name=region.name_en, svg=region.svg_value) for region in db_regions
        ]
    return s.LocationsOut(lang=query.lang, locations=locations, selected=query.selected)
