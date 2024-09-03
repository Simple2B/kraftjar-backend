from pydantic import BaseModel


class AddressBase(BaseModel):
    line1: str = ""
    line2: str = ""
    postcode: str = ""
    city: str = ""
    location_id: int
    street_id: str
    city_id: str


class AddressesFile(BaseModel):
    addresses: list[AddressBase]


class AddressIn(BaseModel):
    pass


class AddressOut(BaseModel):
    pass
