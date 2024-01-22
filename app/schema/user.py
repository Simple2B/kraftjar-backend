from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone: str
    email: str
    is_deleted: bool

    model_config = ConfigDict(
        from_attributes=True,
    )
