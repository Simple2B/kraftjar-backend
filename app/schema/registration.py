# Registration data schema

from pydantic import BaseModel, EmailStr


class RegistrationIn(BaseModel):
    email: EmailStr
    password: str
    fullname: str
    phone: str
