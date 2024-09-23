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
        res = requests.get(CFG.SETTLEMENTS_API_URL)
        # 25396 settlements
        settlements_data = s.SettlementMeestApi.model_validate(res.json())
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting settlements from Meest API",
        )

    settlements_list = settlements_data.result

    with db.begin() as session:
        for settlement in settlements_list:
            settlement_name = settlement.data.n_ua
            city_id = settlement.data.city_id
            district_id = settlement.data.d_id
            kt = settlement.data.kt

            api_settlement_type = settlement.data.t_ua

            if api_settlement_type == CFG.API_VILLAGE:
                type = m.Settlement.type.VILLAGE
            elif api_settlement_type == CFG.API_CITY:
                type = m.Settlement.type.CITY
            else:
                log(log.ERROR, f"Unknown type: {api_settlement_type}")

            db_rayoun = db.session.query(m.Rayon).filter(m.Rayon.district_id == district_id).first()

            if not db_rayoun:
                kyiv = session.query(m.Region).filter(m.Region.id == CFG.KYIV_ID).first()
                log(
                    log.WARNING,
                    f"Rayon not found, settlement: {settlement_name} - set default location to Kyiv (id: {kyiv.id})",
                )

            settlement_db = m.Settlement(
                type=type,
                name_ua=settlement_name,
                name_en="",
                city_id=city_id,
                district_id=district_id,
                location_id=db_rayoun.location_id if db_rayoun else kyiv.id,
                kt=kt,
            )

            session.add(settlement_db)

            if with_print:
                log(log.DEBUG, f"{settlement_db.id}: {settlement_db.name_ua}")

        session.flush()
