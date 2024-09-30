from datetime import datetime
import filetype
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


def mark_as_deleted():
    current_timestamp = datetime.now().strftime("%y-%m-%d_%H:%M:%S")

    return f"deleted-{current_timestamp}"
