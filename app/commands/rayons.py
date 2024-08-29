import time
import requests

from app import models as m
from app import schema as s
from app.database import db
from app.logger import log

from fastapi import HTTPException, status
from config import config

CFG = config()


def get_rayons_from_meest_api(with_print: bool = True):
    """Get rayons from Meest Express Public API"""

    try:
        res = requests.get(CFG.REGIONS_API_URL)
        # 571 rayons
        regions_data = s.RegionMeestApi.model_validate(res.json())
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting regions from Meest API",
        )

    regions_list = regions_data.result

    with db.begin() as session:
        for region in regions_list:
            region_id = region.region_id
            region_name = region.ua

            # Get our region from db by name from Meest API
            db_region = session.query(m.Region).filter(m.Region.name_ua.ilike(f"%{region_name}%")).first()

            if not db_region:
                log(log.ERROR, f"Region not found, region: {region_name}")
                continue

            time.sleep(CFG.DELAY_TIME)

            try:
                res = requests.get(f"{CFG.RAYONS_API_URL}?region_id={region_id}")
                rayons_data = s.RayonMeestApi.model_validate(res.json())
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error getting rayons from Meest API",
                )

            rayons_list = rayons_data.result

            for rayon in rayons_list:
                log(log.INFO, f"Region: {region_name}, Rayon: {rayon.ua}")

                rayon_db = m.Rayon(
                    name_ua=rayon.ua,
                    name_en=rayon.en,
                    location_id=db_region.location_id,
                    district_id=rayon.district_id,
                )

                session.add(rayon_db)

                if with_print:
                    log(log.DEBUG, f"{rayon_db.id}: {rayon_db.name_ua}")

        session.flush()
