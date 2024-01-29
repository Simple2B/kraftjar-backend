import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import schema as s
from app import models as m

from app.logger import log
from config import config

CFG = config()


def get_services(query: s.ServicesIn, db: Session) -> s.ServicesOut:
    main_services = db.scalars(sa.select(m.Service).where(m.Service.parent_id.is_(None))).all()
    all_services: list[s.Service] = []
    for service in main_services:
        all_services.append(
            s.Service(uuid=service.uuid, name=service.name_ua if query.lang == CFG.UA else service.name_en)
        )

    for selected_uuid in query.selected:
        selected_service: m.Service | None = db.scalar(sa.select(m.Service).where(m.Service.uuid == selected_uuid))
        if selected_service:
            for child in selected_service.children:
                all_services.append(
                    s.Service(uuid=child.uuid, name=child.name_ua if query.lang == CFG.UA else child.name_en)
                )
        else:
            log(log.ERROR, "Service with uuid [%s] not found", selected_uuid)
    return s.ServicesOut(lang=query.lang, services=all_services, selected=query.selected)
