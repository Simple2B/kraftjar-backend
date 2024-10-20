from pydantic import BaseModel, ConfigDict
from enum import Enum


class DevicePlatform(Enum):
    IOS = "ios"
    ANDROID = "android"
    UNKNOWN = "unknown"


class DeviceIn(BaseModel):
    push_token: str
    platform: DevicePlatform

    model_config = ConfigDict(
        from_attributes=True,
    )


class DeviceOut(BaseModel):
    device_id: str
    push_token: str

    model_config = ConfigDict(
        from_attributes=True,
    )
