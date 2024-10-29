from functools import cache

import boto3
from mypy_boto3_sns import SNSClient

from config import config


@cache
def get_sns_connect() -> SNSClient:
    settings = config()
    session = boto3.Session(
        aws_access_key_id=settings.AWS_SNS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SNS_SECRET_KEY,
        region_name=settings.AWS_SNS_REGION,
    )
    sns = session.client("sns")

    return sns
