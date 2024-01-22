# Authorization schema
from pydantic import BaseModel


class Auth(BaseModel):
    phone: str
    password: str


class GoogleAuth(BaseModel):
    uid: str
    email: str
    first_name: str | None
    last_name: str | None


class AppleAuth(BaseModel):
    uid: str
    email: str
    first_name: str | None
    last_name: str | None
    display_name: str | None
