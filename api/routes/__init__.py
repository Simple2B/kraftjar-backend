from fastapi import APIRouter, Request

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


@router.get("/list-endpoints/")
def list_endpoints(request: Request):
    url_list = [{"path": route.path, "name": route.name} for route in request.app.routes]
    return url_list
