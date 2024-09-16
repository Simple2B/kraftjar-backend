from functools import cache

import boto3
from mypy_boto3_s3 import S3Client

from config import config


@cache
def get_s3_connect() -> S3Client:
    settings = config()
    session = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY,
    )
    s3 = session.client("s3")
    return s3
