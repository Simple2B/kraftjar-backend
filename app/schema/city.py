from pydantic import BaseModel, ConfigDict
from app.schema.address import AddressOut


class City(BaseModel):
    location_id: int
    district_id: str
    city_id: str
    kt: str
    type: str

    name_ua: str
    name_en: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class CitiesFile(BaseModel):
    cities: list[City]


class CityIn(BaseModel):
    pass


class CityOut(City):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class CityAddressesOut(BaseModel):
    city: City
    addresses: list[AddressOut]
