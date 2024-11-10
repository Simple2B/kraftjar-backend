import json
from fastapi import APIRouter, FastAPI, status
from fastapi.responses import RedirectResponse
from fastapi_pagination import add_pagination

from config import config

from .utils import custom_generate_unique_id
from .routes import router

CFG = config()

router_deep_linking = APIRouter(tags=["deep linking"])

app = FastAPI(
    version=CFG.VERSION,
    generate_unique_id_function=custom_generate_unique_id,
)

app.include_router(router_deep_linking)
app.include_router(router)
add_pagination(app)


# universal links for iOS (deep linking)
@router_deep_linking.get(
    "/.well-known/apple-app-site-association",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def apple_app_link():
    with open("apple-app-site-association.json", "r") as file:
        data = json.load(file)
    return data


# universal links for Android (deep linking)
@router_deep_linking.get(
    "/.well-known/assetlinks.json",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def android_app_link():
    with open("assetlinks.json", "r") as file:
        data = json.load(file)
    return data


@app.get("/", tags=["root"])
async def root():
    return RedirectResponse(url="/docs")
