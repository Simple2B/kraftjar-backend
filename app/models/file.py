from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db

from .utils import ModelMixin
from config import config

CFG = config()


class File(db.Model, ModelMixin):
    __tablename__ = "files"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    name: orm.Mapped[str] = orm.mapped_column(sa.String(256), unique=True)

    original_name: orm.Mapped[str] = orm.mapped_column(sa.String(128))

    type: orm.Mapped[str] = orm.mapped_column(sa.String(64))

    key: orm.Mapped[str] = orm.mapped_column(sa.String(512), unique=True)

    title: orm.Mapped[str] = orm.mapped_column(sa.String(256), server_default="", default="")

    is_deleted: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False)

    updated_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()
    )

    @property
    def url(self):
        return f"{CFG.AWS_S3_BUCKET_URL}{self.key}"

    @property
    def s3_url(self):
        return f"s3://{CFG.AWS_S3_BUCKET_NAME}/{self.key}"

    def mark_as_deleted(self):
        delete_date = datetime.now().strftime("%y-%m-%d_%H:%M:%S")
        delete_suffix = f"-deleted-{delete_date}"
        self.is_deleted = True
        self.name = f"{self.name}{delete_suffix}"
        self.key = f"{self.key}{delete_suffix}"

    def __repr__(self):
        return f"<{self.uuid}:{self.name} >"
