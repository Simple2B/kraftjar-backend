from pydantic import BaseModel, ConfigDict


class Location(BaseModel):
    id: int
    uuid: str
    name: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class LocationList(BaseModel):
    locations: list[Location]

    model_config = ConfigDict(
        from_attributes=True,
    )
