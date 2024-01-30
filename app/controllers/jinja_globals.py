from typing import Sequence

import sqlalchemy as sa

from app import db
from app import models as m


def get_parent_services(service: m.Service) -> Sequence[m.Service]:
    breadcrumb: Sequence[m.Service] = []
    while service.parent_id is not None:
        service = db.session.scalar(sa.select(m.Service).where(m.Service.id == service.parent_id))
        breadcrumb.append(service)
    return breadcrumb[::-1]


def get_neighbors_services(service: m.Service) -> Sequence[m.Service]:
    services: Sequence[m.Service] = db.session.scalars(
        sa.select(m.Service).where(m.Service.parent_id == service.parent_id)
    ).all()
    return services
