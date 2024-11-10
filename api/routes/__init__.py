import json
from fastapi import APIRouter, Request, status

from .user import user_router
from .auth import router as auth_router
from .registration import router as registration_router
from .job import job_router
from .whoami import whoami_router
from .application import application_router
from .location import location_router
from .service import service_router
from .device import device_router
from .rate import rate_router
from .push_notification import push_notification_router

# from .notify import notification_test_router


router = APIRouter(prefix="/api", tags=["API"])

router.include_router(user_router)
router.include_router(auth_router)
router.include_router(registration_router)
router.include_router(job_router)
router.include_router(whoami_router)
router.include_router(application_router)
router.include_router(location_router)
router.include_router(service_router)
router.include_router(device_router)
router.include_router(rate_router)
router.include_router(push_notification_router)

router_linking = APIRouter(tags=["deep linking"])


# universal links for iOS (deep linking)
@router_linking.get(
    "/.well-known/apple-app-site-association",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def apple_app_link():
    with open("apple-app-site-association.json", "r") as file:
        data = json.load(file)
    return data


# universal links for Android (deep linking)
@router_linking.get(
    "/.well-known/assetlinks.json",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def android_app_link():
    with open("assetlinks.json", "r") as file:
        data = json.load(file)
    return data


@router.get("/list-endpoints/")
def list_endpoints(request: Request):
    url_list = [{"path": route.path, "name": route.name} for route in request.app.routes]
    return url_list
