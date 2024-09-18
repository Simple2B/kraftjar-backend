import json
from pathlib import Path

import sqlalchemy as sa

from app import models as m
from app import schema as s
from app.database import db
from app.logger import log

MODULE_PATH = Path(__file__).parent
JSON_FILE_ADDRESSES = MODULE_PATH / ".." / ".." / "data" / "address.json"


def check_if_address_exists(address: s.AddressBase, session: sa.orm.Session):
    """Check if address exists in db"""

    stmt = sa.select(m.Address).where(m.Address.line1 == address.line1)
    db_address = session.scalar(stmt)
    return db_address is not None


def export_addresses_from_json_file(with_print: bool = True):
    """Creates records in address table from json"""

    with open(JSON_FILE_ADDRESSES, "r") as file:
        file_data_addresses = s.AddressesFile.model_validate(json.load(file))

    addresses = file_data_addresses.addresses
    with db.begin() as session:
        for address in addresses:
            if check_if_address_exists(address, session):
                continue

            address_db = m.Address(
                line1=address.line1,
                line2=address.line2,
                postcode=address.postcode,
                city=address.city,
                location_id=address.location_id,
                street_id=address.street_id,
                city_id=address.city_id,
                street_type_ua=address.street_type_ua,
                street_type_en=address.street_type_en,
            )

            session.add(address_db)
            session.flush()
            if with_print:
                log(log.DEBUG, f"{address_db.id}: {address_db.line1}")

    return
