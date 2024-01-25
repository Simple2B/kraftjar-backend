from pydantic import BaseModel, ConfigDict


class Service(BaseModel):
    uuid: str
    name: str


class ServicesIn(BaseModel):
    lang: str = "ua"
    selected: list[str] | None  # list of uuids - selected services


class ServicesOut(BaseModel):
    lang: str = "ua"
    services: list[Service]
    selected: list[str]  # list of uuids - selected services


class ServiceData(BaseModel):
    id: int
    name_ua: str
    name_en: str
    parent_id: int | None
