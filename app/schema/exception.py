from pydantic import BaseModel, ConfigDict


class NotFound(BaseModel):
    description: str = "Record not found"
    model: str = "NotFound"

    model_config = ConfigDict(
        from_attributes=True,
    )
