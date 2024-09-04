# Authorization schema
from pydantic import BaseModel


class Auth(BaseModel):
    phone: str
    password: str


class GoogleAuthIn(BaseModel):
    id_token: str


class GoogleTokenVerification(BaseModel):
    iss: str
    azp: str
    aud: str
    sub: str
    email: str
    email_verified: bool
    name: str | None = None
    picture: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    locale: str | None = None
    iat: int
    exp: int


class AppleAuth(BaseModel):
    uid: str
    email: str
    first_name: str | None
    last_name: str | None
    display_name: str | None


class PhoneAuthIn(BaseModel):
    phone: str
