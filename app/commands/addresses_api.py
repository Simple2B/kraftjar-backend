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


def get_addresses_from_meest_api(lower_limit: int, upper_limit: int, with_print: bool = True):
    """Get addresses from Meest Express Public API"""

    with db.begin() as session:
        db_settlements = (
            session.execute(sa.select(m.Settlement).offset(lower_limit).limit(upper_limit - lower_limit))
            .scalars()
            .all()
        )

        first_element = db_settlements[0]
        last_element = db_settlements[-1]
        log(log.INFO, f"Settlements offset first: {first_element.name_ua}, {first_element.city_id}")
        log(log.INFO, f"Settlements offset last: {last_element.name_ua}, {last_element.city_id}")

        for i, settlement in enumerate(db_settlements):
            every_hundred = (i + 1) % 100 == 0
            first = i == 0
            last = i == len(db_settlements) - 1

            if every_hundred or first or last:
                log(log.INFO, f"Settlement: {settlement.id}, {settlement.name_ua}")

            time.sleep(CFG.DELAY_TIME)
            addresses_api_url = f"{CFG.ADDRESSES_API_URL}?city_id={settlement.city_id}"

            try:
                res = requests.get(addresses_api_url)
                addresses_data = s.AddressMeestApi.model_validate(res.json())

                # I couldn't find the status code types in the API docs
                if addresses_data.status != CFG.SUCCESS_STATUS:
                    log(
                        log.ERROR,
                        f"Error getting addresses from Meest API. Status: {addresses_data.status}, Message: {addresses_data.msg}, Settlement: {settlement.name_ua}, City ID: {settlement.city_id}",
                    )
                    continue

            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error getting addresses from Meest API",
                )

            if not addresses_data.result:
                log(
                    log.WARNING,
                    f"No addresses found for settlement: {settlement.name_ua}, City ID: {settlement.city_id}",
                )
                continue

            addresses_list = addresses_data.result

            for address in addresses_list:
                db_settlement = session.query(m.Settlement).filter(m.Settlement.city_id == address.city_id).first()

                if not db_settlement:
                    kyiv = session.query(m.Region).filter(m.Region.id == CFG.KYIV_ID).first()
                    log(
                        log.WARNING,
                        f"Settlement not found, address: {address.ua} - set default location to Kyiv (id: {kyiv.id})",
                    )

                address_db = m.Address(
                    line1=address.ua,
                    line2=address.en,
                    postcode="",
                    city="",
                    location_id=db_settlement.location_id if db_settlement else kyiv.id,
                    street_id=address.street_id,
                    city_id=address.city_id,
                )

                session.add(address_db)

                if with_print:
                    log(log.DEBUG, f"{address_db.id}: {address_db.line1}")

        session.flush()
