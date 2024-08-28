import sqlalchemy as sa
from app import models as m
from app.database import db

# Run script example
# flask filter-addresses 10 "a1e9f9b8-41b9-11df-907f-00215aee3ebe" "91fc81db-266d-11e7-80fd-1c98ec135263"


def filter_addresses(region_id: int, district_id: str, city_id: str):
    """Filter addresses"""

    with db.begin() as session:
        region = session.execute(sa.select(m.Region).filter_by(id=region_id)).scalar_one_or_none()
        print("Region: ", region)
        print("========================================================================================")

        if not region:
            print("Region not found")
            session.close()
            return

        rayons = session.query(m.Rayon).filter(m.Rayon.location_id == region.id).all()
        print("Rayons: ", rayons)
        print("========================================================================================")

        if not rayons:
            print("Rayons not found")
            session.close()
            return

        settlements = session.query(m.Settlement).filter(m.Settlement.district_id == district_id).all()
        print("Settlements: ", settlements)
        print("========================================================================================")

        if not settlements:
            print("Settlements not found")
            session.close()
            return

        addresses = session.query(m.Address).filter(m.Address.city_id == city_id).all()
        print("Addresses: ", addresses)

        session.close()

    return
