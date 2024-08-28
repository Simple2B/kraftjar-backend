from typing import TYPE_CHECKING
import enum
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db

from .utils import ModelMixin

if TYPE_CHECKING:
    from .location import Location


class Settlement(db.Model, ModelMixin):
    __tablename__ = "settlements"

    class Type(enum.Enum):
        REGION_CENTER = "region_center"
        RAYON_CENTER = "rayon_center"
        CITY = "city"
        VILLAGE = "village"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    location_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("locations.id"))

    # From Meest Express Public API
    district_id: orm.Mapped[str] = orm.mapped_column(sa.String(36))
    city_id: orm.Mapped[str] = orm.mapped_column(sa.String(36))
    # Класифікатор об'єктів адміністративно-територіального устрою України
    kt: orm.Mapped[str] = orm.mapped_column(sa.String(36))

    type: orm.Mapped[Type] = orm.mapped_column(sa.Enum(Type))

    name_ua: orm.Mapped[str] = orm.mapped_column(sa.String(128))
    name_en: orm.Mapped[str] = orm.mapped_column(sa.String(128))

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        default=datetime.utcnow,
    )
    updated_at: orm.Mapped[datetime] = orm.mapped_column(
        default=sa.func.now(),
        onupdate=sa.func.now(),
    )
    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)

    # Relationships
    location: orm.Mapped["Location"] = orm.relationship()

    def __repr__(self):
        return f"<{self.id}:{self.name_ua} >"
