from typing import Sequence

from pydantic import BaseModel, ConfigDict


class FieldCreate(BaseModel):
    name_ua: str
    name_en: str
    services: Sequence[str]

    model_config = ConfigDict(
        from_attributes=True,
    )
