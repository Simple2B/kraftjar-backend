# Registration data schema

from enum import Enum
from pydantic import BaseModel, EmailStr

MIN_LENGTH = 4
SPECIAL_CHARS = '[!@#$%^&*()_,.?":{}|<>]'


class PasswordStrength(Enum):
    EASY_HACK = "easy_hack"
    WEAK = "weak"
    GOOD = "good"
    STRONG = "strong"
    SECURE = "secure"


weakest_passwords = [
    "123456",
    "password",
    "123456789",
    "12345a",
    "qwerty",
    "111111",
    "123123",
    "abc123",
    "password1",
    "пароль",
]


class RegistrationIn(BaseModel):
    email: EmailStr | None = None
    fullname: str
    services: list[str] = []  # uuids of selected services
    locations: list[str] = []  # uuids of selected locations
    is_volunteer: bool = False

    #############################################################################
    # NOTE: We currently don't use manual registration and verification by phone.
    # Perhaps it will be useful in the future.
    #############################################################################

    # password: str
    # password_strength: PasswordStrength | None = None
    # phone: str

    # @field_validator("password")
    # @classmethod
    # def password_validation(cls, value: str):
    #     if len(value) < MIN_LENGTH:
    #         raise ValueError(f"password must be at least {MIN_LENGTH} characters long")
    #     return value

    # @field_validator("password_strength")
    # @classmethod
    # def password_strength_validator(cls, value: str):
    #     if not value:
    #         return None

    #     has_uppercase = any(c.isupper() for c in value)
    #     has_lowercase = any(c.islower() for c in value)
    #     has_digit = any(c.isdigit() for c in value)
    #     has_special_char = any(c in SPECIAL_CHARS for c in value)

    #     if value in weakest_passwords:
    #         return PasswordStrength.EASY_HACK.value

    #     if has_lowercase and has_uppercase and has_digit and has_special_char:
    #         return PasswordStrength.SECURE.value
    #     elif has_lowercase and has_uppercase and has_digit:
    #         return PasswordStrength.STRONG.value
    #     elif has_lowercase and has_uppercase:
    #         return PasswordStrength.GOOD.value
    #     else:
    #         return PasswordStrength.WEAK.value


class PhoneVerificationIn(BaseModel):
    phone: str
    otp_code: str


class ChangePasswordIn(BaseModel):
    phone: str
    password: str


class SetPhoneIn(BaseModel):
    phone: str


class SetPhoneOut(BaseModel):
    phone: str


class ValidatePhoneIn(BaseModel):
    code: str
