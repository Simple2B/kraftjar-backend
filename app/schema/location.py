import enum
from pydantic import BaseModel, ConfigDict

from app.schema.language import Language


class SettlementType(enum.Enum):
    REGION_CENTER = "region_center"
    RAYON_CENTER = "rayon_center"
    CITY = "city"
    VILLAGE = "village"


class Location(BaseModel):
    uuid: str
    name: str
    svg: str | None = None

    __hash__ = object.__hash__


class LocationStrings(BaseModel):
    uuid: str
    name: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class LocationsIn(BaseModel):
    lang: str
    selected: list[str]  # uuids of selected locations


class LocationsOut(BaseModel):
    lang: str
    locations: list[Location]
    selected: list[str]  # uuids of selected locations


class Region(BaseModel):
    name_ua: str
    name_en: str
    svg: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class RegionsFile(BaseModel):
    regions: list[Region]


# schame for test
class LocationOut(BaseModel):
    id: int
    uuid: str


class LocationsFile(BaseModel):
    locations: list[LocationOut]


class LocationsListIn(BaseModel):
    lang: Language


class LocationsListOut(BaseModel):
    locations: list[LocationStrings]


class Rayon(BaseModel):
    location_id: int
    district_id: str
    name_ua: str
    name_en: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class RayonsList(BaseModel):
    rayons: list[Rayon]


class Settlement(BaseModel):
    uuid: str
    location: str


class SettlementsListOut(BaseModel):
    settlements: list[Settlement]


class AddressIn(BaseModel):
    uuid: str
    query: str
    lang: Language


class AddressOutput(BaseModel):
    uuid: str
    name: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class AddressesListOut(BaseModel):
    addresses: list[AddressOutput]
