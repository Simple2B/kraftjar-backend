# Registration data schema

from pydantic import BaseModel, EmailStr, field_validator

MIN_LENGTH = 8
SPECIAL_CHARS = '[!@#$%^&*()_,.?":{}|<>]'

class RegistrationIn(BaseModel):
    email: EmailStr
    password: str
    fullname: str
    phone: str
    services: list[str] = []  # uuids of selected services
    locations: list[str] = []  # uuids of selected locations
    is_volunteer: bool = False

    @field_validator('password')
    @classmethod
    def password_validation(cls, v: str) -> str:
        if len(v) < MIN_LENGTH:
            raise ValueError('password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('password must contain at least one digit')
        if not any(c in SPECIAL_CHARS for c in v):
            raise ValueError('password must contain at least one special character')
        return v


class SetPhoneIn(BaseModel):
    phone: str


class SetPhoneOut(BaseModel):
    phone: str


class ValidatePhoneIn(BaseModel):
    code: str
