from datetime import datetime
import filetype
from fastapi import UploadFile, HTTPException, status
from fastapi.routing import APIRoute
import app.models as m

from app.logger import log
from app.schema.language import Language


def custom_generate_unique_id(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"


def get_file_extension(file: UploadFile):
    extension = filetype.guess_extension(file.file)

    if not extension:
        log(log.ERROR, "Extension not found for image [%s]", file.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Extension not found")

    return extension


def mark_as_deleted():
    current_timestamp = datetime.now().strftime("%y-%m-%d_%H:%M:%S:%f")

    return f"deleted-{current_timestamp}"


def format_location_string(location: m.Location, address: m.Address, lang: Language):
    ALL_UKRAINE = "Вся Україна" if lang == Language.UA else "All Ukraine"
    job_location = ALL_UKRAINE

    if location:
        job_location = location.region[0].name_ua if lang == Language.UA else location.region[0].name_en

    job_address = None
    if address:
        lang_name = address.line1 if lang == Language.UA else address.line2
        lang_type = address.street_type_ua if lang == Language.UA else address.street_type_en
        job_address = f"{lang_type} {lang_name}"

    return (job_location, job_address)
