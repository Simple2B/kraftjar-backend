# Authorization schema
from pydantic import BaseModel, ConfigDict
from enum import Enum


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


class AppleAuthTokenIn(BaseModel):
    id_token: str


class AppleAuthenticationFullName(BaseModel):
    givenName: str | None = None
    familyName: str | None = None


class AppleTokenVerification(BaseModel):
    iss: str
    aud: str
    exp: int
    iat: int
    sub: str
    c_hash: str
    email: str
    email_verified: bool
    auth_time: int
    nonce_supported: bool
    fullName: AppleAuthenticationFullName | None = None


class PhoneAuthIn(BaseModel):
    phone: str


class AuthType(Enum):
    BASIC = "basic"
    GOOGLE = "google"
    APPLE = "apple"
    DIIA = "diia"


class AuthAccount(BaseModel):
    user_id: int
    email: str
    auth_type: AuthType
    oauth_id: str = ""

    model_config = ConfigDict(
        from_attributes=True,
    )

class AuthAccountOut(BaseModel):
    email: str
    auth_type: AuthType
