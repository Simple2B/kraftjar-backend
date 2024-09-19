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
    response_model=list[s.CityAddressesOut],
    dependencies=[Depends(get_current_user)],
)
def get_address(
    query: str = "",
    lang: s.Language = s.Language.UA,
    db: Session = Depends(get_db),
):
    """Returns the address"""

    cities_lang_column = m.Settlement.name_ua if lang == s.Language.UA else m.Settlement.name_en

    cities: Sequence[m.Settlement] = db.scalars(
        sa.select(m.Settlement).where(cities_lang_column.ilike(f"%{query}%"))
    ).all()

    log(log.INFO, "Found %s cities", len(cities))

    cities_ids = [city.city_id for city in cities]

    addresses_cities = db.scalars(sa.select(m.Address).where(m.Address.city_id.in_(cities_ids))).all()

    log(log.INFO, "Found %s addresses", len(addresses_cities))

    city_addresses_out = []
    for city in cities:
        city_addresses = [address for address in addresses_cities if address.city_id == city.city_id]

        city_addresses_out.append(
            s.CityAddressesOut(
                city=s.City.model_validate(city),
                addresses=[s.AddressOut.model_validate(address) for address in city_addresses],
            )
        )

    log(log.INFO, "City [%s] has %s addresses", city.name_ua, len(city_addresses))

    return city_addresses_out
