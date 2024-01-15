from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone: str
    email: str
    activated: bool = True

    model_config = ConfigDict(
        from_attributes=True,
    )
