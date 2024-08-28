import requests
from app import models as m
from app import schema as s
from app.database import db
from app.logger import log
from fastapi import HTTPException, status
from config import config

CFG = config()


def get_settlements_from_meest_api(with_print: bool = True):
    """Get settlements from Meest Express Public API"""

    try:
        settlements = requests.get(CFG.SETTLEMENTS_API_URL)
        # 25396 settlements
        settlements_data: s.SettlementMeestApi = settlements.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting settlements from Meest API",
        )

    settlements_list: list[s.SettlementList] = settlements_data["result"]

    for settlement in settlements_list:
        type = settlement["data"]["t_ua"]
        settlement_name = settlement["data"]["n_ua"]
        city_id = settlement["data"]["city_id"]
        district_id = settlement["data"]["d_id"]
        kt = settlement["data"]["kt"]
        print(settlement_name)

        if type == "місто":
            type = m.Settlement.Type.CITY
        elif type == "село":
            type = m.Settlement.Type.VILLAGE
        else:
            print("Unknown type", type)

        db_rayoun = db.session.query(m.Rayon).filter(m.Rayon.district_id == district_id).first()

        if not db_rayoun:
            print("Region not found", db_rayoun)
            continue

        with db.begin() as session:
            settlement_db = m.Settlement(
                type=type,
                name_ua=settlement_name,
                name_en="",
                city_id=city_id,
                district_id=district_id,
                location_id=db_rayoun.location_id,
                kt=kt,
            )

            session.add(settlement_db)
            session.flush()
            if with_print:
                log(log.DEBUG, f"{settlement_db.id}: {settlement_db.name_ua}")

    return
