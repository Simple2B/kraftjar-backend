from pydantic import BaseModel, ConfigDict


class Profession(BaseModel):
    id: int
    uuid: str
    name: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class ProfessionList(BaseModel):
    professions: list[Profession]

    model_config = ConfigDict(
        from_attributes=True,
    )
