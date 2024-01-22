# Registration data schema

from pydantic import BaseModel, Field, EmailStr


class RegistrationIn(BaseModel):
    email: EmailStr = Field(..., example="user@kraftjar.net")
    password: str = Field(..., example="********")
    fullname: str = Field(..., example="Svjatyj Mykolay")
    phone: str = Field(..., example="+380 67 123 4567")
