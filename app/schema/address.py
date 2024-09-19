from pydantic import BaseModel, ConfigDict


class AddressBase(BaseModel):
    line1: str = ""
    line2: str = ""
    postcode: str = ""
    city: str = ""
    location_id: int
    street_id: str
    city_id: str
    street_type_ua: str = ""
    street_type_en: str = ""

    model_config = ConfigDict(
        from_attributes=True,
    )


class AddressesFile(BaseModel):
    addresses: list[AddressBase]


class AddressIn(BaseModel):
    pass


class AddressOut(AddressBase):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )
