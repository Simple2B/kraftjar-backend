import json
from fastapi import APIRouter, status

from config import config

CFG = config()

router_deep_linking = APIRouter(
    prefix="/.well-known",
    tags=["deep linking"],
)


# universal links for iOS (deep linking)
@router_deep_linking.get(
    "/apple-app-site-association",
    status_code=status.HTTP_200_OK,
)
def apple_app_link():
    with open("apple-app-site-association.json", "r") as file:
        data = json.load(file)
    return data


# universal links for Android (deep linking)
@router_deep_linking.get(
    "/assetlinks.json",
    status_code=status.HTTP_200_OK,
)
def android_app_link():
    with open("assetlinks.json", "r") as file:
        data = json.load(file)
    return data
