# Registration data schema

from pydantic import BaseModel, EmailStr


class RegistrationIn(BaseModel):
    email: EmailStr
    password: str
    fullname: str
    phone: str
    services: list[str] = []  # uuids of selected services
    locations: list[str] = []  # uuids of selected locations
    is_volunteer: bool = False


class SetPhoneIn(BaseModel):
    phone: str


class ValidatePhoneIn(BaseModel):
    code: str
