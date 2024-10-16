from pydantic import BaseModel, ConfigDict


class DeviceIn(BaseModel):
    push_token: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class DeviceOut(BaseModel):
    device_id: str
    push_token: str

    model_config = ConfigDict(
        from_attributes=True,
    )
