import re
from uuid import uuid4
from fastapi import UploadFile, status, HTTPException
from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app import schema as s
from app import models as m

from app.logger import log
from config import config

S3_UPLOAD_EXTRAS = {"ACL": "public-read-write"}

RE_SPECIAL_CHARACTERS = "[^a-zA-Z0-9 \n\.]"


CFG = config()


def create_file(
    file: UploadFile,
    db: Session,
    s3_client: S3Client,
    extension: str,
    file_type: s.FileType,
    content_type_override: str | None = None,
    file_name_url: str = "",
) -> m.File:
    try:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File name is required",
            )
        filename_without_special_characters = re.sub(RE_SPECIAL_CHARACTERS, "", file.filename)
        filename_without_spaces = filename_without_special_characters.replace(" ", "_")
        file_uuid = str(uuid4())
        filename = f"{file_uuid}_{filename_without_spaces}"
        short_name = filename.split(".")[0]

        key = f"{file_name_url}/{short_name}" + f".{extension}"
        log(log.INFO, "[create_file] key is %s", key)

        # Create a BytesIO stream from the file bytes

        extras = {
            **S3_UPLOAD_EXTRAS,
        }

        if content_type_override:
            extras["ContentType"] = content_type_override

        s3_client.upload_fileobj(
            file.file,  # Pass the BytesIO stream
            CFG.AWS_S3_BUCKET_NAME,
            key,
            ExtraArgs=extras,
        )

        file_model = m.File(
            type=file_type.value,
            uuid=file_uuid,
            original_name=file.filename,
            name=filename,
            key=key,
        )
        db.add(file_model)
        db.commit()
        db.refresh(file_model)
        log(log.INFO, "[create_file] file [%s] was created", file_model.name)
        return file_model
    except ClientError as e:
        log(log.ERROR, "[create_file] Error uploading file to S3 - [%s]", e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error while uploading file to storage",
        )
    except SQLAlchemyError as e:
        log(log.INFO, "[create_file] file [%s] was not created:\n %s", file_model.name, e)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="file exists")


def delete_file(
    db: Session,
    file: m.File,
    s3_client: S3Client,
) -> None:
    try:
        s3_client.delete_object(Bucket=CFG.AWS_S3_BUCKET_NAME, Key=file.key)
    except ClientError as e:
        log(log.ERROR, "Error deleting file from S3 - [%s]", e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error occurred while deleting file from S3",
        )
    try:
        db.delete(file)
        db.commit()
    except SQLAlchemyError as e:
        log(log.INFO, "file [%s] was not deleted:\n %s", file.name, e)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="file exists")


def is_image_file(extension: str) -> bool:
    return extension.lower() in ("jpg", "jpeg", "png", "gif", "webp", "avif")


def is_video_file(extension: str) -> bool:
    return extension.lower() in ("mp4", "mov", "avi", "flv", "wmv")


def get_file_type(extension: str) -> s.FileType:
    if is_image_file(extension):
        return s.FileType.IMAGE
    elif is_video_file(extension):
        return s.FileType.VIDEO
    else:
        return s.FileType.UNKNOWN
