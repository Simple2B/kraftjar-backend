import requests
import time

import sqlalchemy as sa

from app import models as m
from app import schema as s
from app.database import db
from app.logger import log

from fastapi import HTTPException, status
from config import config

CFG = config()


def get_addresses_from_meest_api(with_print: bool = True):
    """Get addresses from Meest Express Public API"""

    db_settlements = db.session.execute(sa.select(m.Settlement)).scalars().all()

    # 3 seconds multiplied by 25500 equals 21.25 hours.

    # Idea: make 1000 records per script run. Then check if the address already exists.
    # 3 seconds multiplied by 1000 equals 50 minutes.

    for settlement in db_settlements:
        time.sleep(3)
        addresses_api_url = f"{CFG.ADDRESSES_API_URL}?city_id={settlement.city_id}"

        try:
            addresses = requests.get(addresses_api_url)
            addresses_data: s.AddressMeestApi = addresses.json()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error getting addresses from Meest API",
            )

        addresses_list: list[s.AddressList] = addresses_data["result"]

        for address in addresses_list:
            print(address["ua"])
            db_settlement = db.session.query(m.Settlement).filter(m.Settlement.city_id == address["city_id"]).first()

            if not db_settlement:
                print("Settlement not found", db_settlement)
                continue

            with db.begin() as session:
                address_db = m.Address(
                    line1=address["ua"],
                    line2=address["en"],
                    postcode="",
                    city="",
                    location_id=db_settlement.location_id,
                    street_id=address["street_id"],
                    city_id=address["city_id"],
                )

                session.add(address_db)
                session.flush()
                if with_print:
                    log(log.DEBUG, f"{address_db.id}: {address_db.line1}")

    return
