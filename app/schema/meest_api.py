from pydantic import BaseModel


class RegionList(BaseModel):
    ua: str
    ru: str
    en: str
    region_id: str
    kt: str


class RegionMeestApi(BaseModel):
    status: int
    msg: str | None
    result: list[RegionList]


class RayonList(BaseModel):
    ua: str
    ru: str
    en: str
    district_id: str
    region_id: str
    kt: str


class RayonMeestApi(BaseModel):
    status: int
    msg: str | None
    result: list[RayonList]


class SettlementData(BaseModel):
    n_ua: str
    n_ru: str
    t_ua: str
    city_id: str
    kt: str
    reg: str
    reg_id: str
    dis: str
    d_id: str
    is_delivery_in_city: bool


class SettlementList(BaseModel):
    data: SettlementData


class SettlementMeestApi(BaseModel):
    status: int
    msg: str | None
    result: list[SettlementList]


class AddressList(BaseModel):
    ua: str
    ru: str
    en: str
    t_ua: str
    t_ru: str
    t_en: str
    street_id: str
    city_id: str
    kt: str


class AddressMeestApi(BaseModel):
    status: int
    msg: str | None
    result: list[AddressList]
