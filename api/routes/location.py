import re
from typing import Sequence
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import sqlalchemy as sa

import app.schema as s
from api import controllers as c
from api.dependency.user import get_current_user
from app import models as m
from app.database import get_db
from app.logger import log
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
    "/all",
    status_code=status.HTTP_200_OK,
    response_model=s.LocationsListOut,
)
def get_all_locations(
    lang: s.Language = s.Language.UA,
    db: Session = Depends(get_db),
):
    """Returns all locations"""

    db_locations = db.scalars(sa.select(m.Location)).all()

    locations_out = [
        s.LocationStrings(
            name=location.region[0].name_ua if lang == s.Language.UA else location.region[0].name_en,
            uuid=location.uuid,
        )
        for location in db_locations
    ]

    return s.LocationsListOut(locations=locations_out)


@location_router.get(
    "/settlements",
    status_code=status.HTTP_200_OK,
    response_model=s.SettlementsListOut,
    dependencies=[Depends(get_current_user)],
)
def get_settlements(
    query: str = "",
    lang: s.Language = s.Language.UA,
    db: Session = Depends(get_db),
):
    """Returns the settlements"""

    if not query:
        log(log.ERROR, "Query is empty")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query is empty")

    wordList = re.sub(CFG.RE_WORD, " ", query).split()

    settlements_name_lang = m.Settlement.name_ua if lang == s.Language.UA else m.Settlement.name_en
    lookups = [settlements_name_lang.ilike(f"%{keyword}%") for keyword in wordList]

    # City first
    type_order = sa.desc(m.Settlement.type == s.SettlementType.CITY.name)
    settlements: Sequence[m.Settlement] = db.scalars(sa.select(m.Settlement).where(*lookups).order_by(type_order)).all()

    if not settlements:
        log(log.INFO, "Settlements not found by query [%s]", query)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settlements not found")

    rayons_ids = [settlement.district_id for settlement in settlements]

    rayons = db.scalars(sa.select(m.Rayon).where(m.Rayon.district_id.in_(rayons_ids))).all()
    if not rayons:
        log(log.INFO, "Rayons not found by query [%s]", query)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rayons not found")

    settlements_data_out = []

    for settlement in settlements:
        if settlement.type == s.SettlementType.CITY.name:
            type = "м. " if lang == s.Language.UA else "c. "
        elif settlement.type == s.SettlementType.VILLAGE.name:
            type = "с. " if lang == s.Language.UA else "v. "
        else:
            type = ""

        rayon = [rayon for rayon in rayons if rayon.district_id == settlement.district_id][0]
        rayon_name = rayon.name_ua
        region_name = rayon.location.region[0].name_ua

        settlements_data_out.append(
            s.Settlement(
                uuid=settlement.city_id,
                location=f"{type}{settlement.name_ua}, район {rayon_name}, {region_name}",
            )
        )

    return s.SettlementsListOut(settlements=settlements_data_out)


@location_router.get(
    "/addresses",
    status_code=status.HTTP_200_OK,
    response_model=s.AddressesListOut,
    dependencies=[Depends(get_current_user)],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Addresses not found"},
    },
)
def get_addresses(
    query: str = "",
    uuid: str = "",
    lang: s.Language = s.Language.UA,
    db: Session = Depends(get_db),
):
    """Returns the addresses by settlement uuid"""

    if not query:
        log(log.ERROR, "Query is empty")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query is empty")

    if not uuid:
        log(log.ERROR, "UUID must be provided")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UUID must be provided")

    wordList = re.sub(CFG.RE_WORD, " ", query).split()
    is_ua_lang = lang == s.Language.UA

    address_name_lang = m.Address.line1 if is_ua_lang else m.Address.line2

    lookups = [address_name_lang.ilike(f"%{keyword}%") for keyword in wordList]
    address_filter = sa.and_(*lookups, m.Address.city_id == uuid)
    addresses: Sequence[m.Address] = db.scalars(sa.select(m.Address).where(address_filter)).all()

    if not addresses:
        log(log.INFO, "Addresses not found by query [%s]", query)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Addresses not found")

    addresses_list: list[s.AddressOutput] = []

    for address in addresses:
        name_lang = address.line1 if is_ua_lang else address.line2
        type_lang = address.street_type_ua if is_ua_lang else address.line2

        addresses_list.append(s.AddressOutput(uuid=address.street_id, name=f"{type_lang.lower()} {name_lang}"))

    return s.AddressesListOut(addresses=addresses_list)
