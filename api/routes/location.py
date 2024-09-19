import re
from typing import Sequence
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
import sqlalchemy as sa

import app.schema as s
from api import controllers as c
from api.dependency.user import get_current_user
from app import models as m
from app.database import get_db
from app.logger import log
from app import schema as s
from config import config

CFG = config()

location_router = APIRouter(prefix="/locations", tags=["Location"])


@location_router.post(
    "",
    status_code=status.HTTP_200_OK,
    response_model=s.LocationsOut,
)
def get_locations(query: s.LocationsIn, db: Session = Depends(get_db)):
    return c.get_locations(query, db)


@location_router.get(
    "/address",
    status_code=status.HTTP_200_OK,
    response_model=s.CitiesAddresses,
    dependencies=[Depends(get_current_user)],
)
def get_address(
    query: str = "",
    lang: s.Language = s.Language.UA,
    db: Session = Depends(get_db),
):
    """Returns the address"""

    if not query:
        return []

    cities_lang_column = m.Settlement.name_ua if lang == s.Language.UA else m.Settlement.name_en

    cities_addresses_list: list[s.CityAddressesOut] = []
    wordList = re.sub(CFG.RE_WORD, " ", query).split()
    for word in wordList:
        if len(word) >= 3:
            cities: Sequence[m.Settlement] = db.scalars(
                sa.select(m.Settlement).where(cities_lang_column.ilike(f"%{word}%"))
            ).all()
            cities_ids = [city.city_id for city in cities]

            log(log.INFO, "Found %s cities", len(cities))

            cities_addresses = db.scalars(sa.select(m.Address).where((m.Address.city_id.in_(cities_ids)))).all()

            for city in cities:
                city_addresses = [address for address in cities_addresses if address.city_id == city.city_id]

                cities_addresses_list.append(
                    s.CityAddressesOut(
                        city=s.City.model_validate(city),
                        addresses=[s.AddressOut.model_validate(address) for address in city_addresses],
                    )
                )

    cities_addresses_list

    city_addresses_out: list[s.CityAddresse] = []

    # for city_addresses in cities_addresses_list:
    #     city_addresses
    # city_addresses_out.append(
    #     s.CityAddresse(
    #         uuid=city_addresses.addresses.uuid,
    #         city_addresses=f"{city_addresses.city.name_ua}, {city_addresses.addresses.street_type_ua} {city_addresses.addresses.line1}",
    #     )
    # )

    return city_addresses_out
