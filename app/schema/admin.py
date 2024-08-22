from pydantic import BaseModel, ConfigDict


class Admin(BaseModel):
    id: int
    username: str
    email: str
    is_deleted: bool

    model_config = ConfigDict(
        from_attributes=True,
    )
