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

    with db.begin() as session:
        db_settlements = session.execute(sa.select(m.Settlement)).scalars().all()

        for settlement in db_settlements:
            print(settlement.name_ua)

            time.sleep(CFG.DELAY_TIME)
            addresses_api_url = f"{CFG.ADDRESSES_API_URL}?city_id={settlement.city_id}"

            try:
                res = requests.get(addresses_api_url)
                addresses_data = s.AddressMeestApi.model_validate(res.json())
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error getting addresses from Meest API",
                )

            addresses_list = addresses_data.result

            for address in addresses_list:
                db_settlement = session.query(m.Settlement).filter(m.Settlement.city_id == address.city_id).first()

                if not db_settlement:
                    print("Settlement not found, address:", address.ua)
                    continue

                address_db = m.Address(
                    line1=address.ua,
                    line2=address.en,
                    postcode="",
                    city="",
                    location_id=db_settlement.location_id,
                    street_id=address.street_id,
                    city_id=address.city_id,
                )

                session.add(address_db)

                if with_print:
                    log(log.DEBUG, f"{address_db.id}: {address_db.line1}")

        session.flush()
    return
