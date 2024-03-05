from datetime import datetime
from pydantic import BaseModel, ConfigDict

from config import config

CFG = config()


class Service(BaseModel):
    uuid: str
    name: str

    __hash__ = object.__hash__


class ServiceDB(BaseModel):
    id: int
    uuid: str
    name_ua: str
    name_en: str
    parent_id: int | None = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False

    model_config = ConfigDict(
        from_attributes=True,
    )


class ServicesIn(BaseModel):
    lang: str = CFG.UA
    selected: list[str] = []  # list of uuids - selected services


class ServicesOut(BaseModel):
    lang: str
    services: list[Service]
    selected: list[str]  # list of uuids - selected services


class ServiceData(BaseModel):
    id: int
    name_ua: str
    name_en: str
    parent_id: int | None = None
    db_id: int | None = None  # id in db


class ServiceDataFile(BaseModel):
    services: list[ServiceData]
