from pydantic import BaseModel, ConfigDict


class Service(BaseModel):
    id: int
    uuid: str
    name: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class ServiceList(BaseModel):
    services: list[Service]

    model_config = ConfigDict(
        from_attributes=True,
    )
