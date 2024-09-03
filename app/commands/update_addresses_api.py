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


def update_addresses_from_meest_api(lower_limit: int, upper_limit: int, with_print: bool = True):
    """Update addresses from Meest Express Public API"""

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

            street_ids = [address.street_id for address in addresses_list]
            db_addresses = session.query(m.Address).filter(m.Address.street_id.in_(street_ids)).all()

            if not db_addresses:
                log(log.WARNING, f"No addresses found in DB for settlement: {settlement.name_ua}, City ID: {settlement.city_id}")

            db_address_map = {db_address.street_id: db_address for db_address in db_addresses}

            update_data = []

            for address in addresses_list:
                db_address = db_address_map.get(address.street_id)

                if db_address:
                    update_data.append(
                        {"id": db_address.id, "street_type_ua": address.t_ua, "street_type_en": address.t_en}
                    )
                    if with_print:
                        log(log.DEBUG, f"{db_address.id}: {db_address.line1}")
                else:
                    log(
                        log.WARNING,
                        f"№{i} Address not found in DB: {address.ua}, City ID: {address.city_id} Street ID: {address.street_id}",
                    )

            session.bulk_update_mappings(m.Address, update_data)
        session.flush()
