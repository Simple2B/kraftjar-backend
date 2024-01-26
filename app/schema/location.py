from pydantic import BaseModel


class Location(BaseModel):
    uuid: str
    name: str
    svg: str | None = None


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


class RegionsFile(BaseModel):
    regions: list[Region]
