import filetype
import re
from fastapi import UploadFile, HTTPException, status
from fastapi.routing import APIRoute

from app.logger import log


def custom_generate_unique_id(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"


def get_file_extension(file: UploadFile):
    extension = filetype.guess_extension(file.file)

    if not extension:
        log(log.ERROR, "Extension not found for image [%s]", file.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Extension not found")

    return extension


def password_validation(password: str) -> None:
    MIN_LENGTH = 8
    LOWER_CASE = r"[a-z]"
    UPPER_CASE = r"[A-Z]"
    DIGITS = r"[0-9]"
    SPECIAL_CHARS = r'[!@#$%^&*()_,.?":{}|<>]'

    if len(password) < MIN_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Password must be at least 8 characters long"
        )

    if not re.search(LOWER_CASE, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Password must contain at least one lowercase letter"
        )

    if not re.search(UPPER_CASE, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Password must contain at least one uppercase letter"
        )

    if not re.search(DIGITS, password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password must contain at least one digit")

    if not re.search(SPECIAL_CHARS, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Password must contain at least one special character"
        )
