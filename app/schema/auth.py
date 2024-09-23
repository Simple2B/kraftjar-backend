# Authorization schema
from pydantic import BaseModel, ConfigDict
from enum import Enum


class Auth(BaseModel):
    phone: str
    password: str


class GoogleAuthIn(BaseModel):
    id_token: str


class GoogleTokenVerification(BaseModel):
    # These six fields are included in all Google ID Tokens.
    # The issuer, or signer, of the token. For Google-signed ID tokens, this value is https://accounts.google.com.
    iss: str
    # authorized party, Who the token was issued to.
    azp: str
    # The audience of the token. The value of this claim must match the application or service that uses the token to authenticate the request. For more information, see ID token aud claim.
    aud: str
    # The subject: the ID that represents the principal making the request.
    # (Next.js takes this field as the main user ID)
    sub: str
    # issued at
    iat: int
    # expiration time
    exp: int
    # These seven fields are only included when the user has granted the "profile" and "email" OAuth scopes to the application.
    email: str
    email_verified: bool
    name: str | None = None
    picture: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    locale: str | None = None


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
    id: int
    email: str = ""
    auth_type: AuthType
