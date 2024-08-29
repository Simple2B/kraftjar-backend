import sqlalchemy as sa
from app import models as m
from app.database import db

from app.logger import log

# Run script example
# flask filter-addresses 10 "a1e9f9b8-41b9-11df-907f-00215aee3ebe" "91fc81db-266d-11e7-80fd-1c98ec135263"


def filter_addresses(region_id: int, district_id: str, city_id: str):
    """Filter addresses"""

    with db.begin() as session:
        region = session.execute(sa.select(m.Region).filter_by(id=region_id)).scalar_one_or_none()
        log(log.INFO, f"Region: {region}")
        print("========================================================================================")

        if not region:
            log(log.ERROR, f"Region not found, id: {region_id}")
            return

        rayons = session.query(m.Rayon).filter(m.Rayon.location_id == region.id).all()
        log(log.INFO, f"Rayons: {rayons}")
        print("========================================================================================")

        if not rayons:
            log(log.ERROR, f"Rayons not found, region id: {region.id}")
            return

        settlements = session.query(m.Settlement).filter(m.Settlement.district_id == district_id).all()
        log(log.INFO, f"Settlements: {settlements}")
        print("========================================================================================")

        if not settlements:
            log(log.ERROR, f"Settlements not found, rayon id: {district_id}")
            return

        addresses = session.query(m.Address).filter(m.Address.city_id == city_id).all()
        log(log.INFO, f"Addresses: {addresses}")
