import os
from functools import lru_cache
import tomllib
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_ENV = os.environ.get("APP_ENV", "development")


def get_version() -> str:
    with open("pyproject.toml", "rb") as f:
        return tomllib.load(f)["tool"]["poetry"]["version"]


class BaseConfig(BaseSettings):
    """Base configuration."""

    IS_API: bool = False

    ENV: str = "base"
    APP_NAME: str = "Kraftjar"
    SECRET_KEY: str
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    WTF_CSRF_ENABLED: bool = False
    VERSION: str = get_version()

    # Mail config
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_USE_TLS: bool
    MAIL_USE_SSL: bool
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_DEFAULT_SENDER: str

    # Super admin
    ADMIN_USERNAME: str
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str

    # Pagination
    DEFAULT_PAGE_SIZE: int
    PAGE_LINKS_NUMBER: int

    # API
    JWT_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Business logic

    MINIMUM_RATE: int = 1
    MAXIMUM_RATE: int = 5

    UA: str = "ua"
    EN: str = "en"

    MAX_USER_SEARCH_RESULTS: int = 10
    MAX_JOBS_SEARCH_RESULTS: int = 15

    # for test data from google spreadsheets

    SCOPES: list[str] = ["https://www.googleapis.com/auth/spreadsheets"]
    SPREADSHEET_ID: str = "1Hw5Oh9vtwuPUYJkSGo0uGikRbHeiM52SNdUxwXFU3hQ"

    ALL_UKRAINE: str = "all-ukraine"
    RE_WORD: str = "[^\w]"

    TEST_USER_PASSWORD: str = "Kraftjar2024"

    USER_CAROUSEL_LIMIT: int = 16

    # Meest Public API
    SUCCESS_STATUS: int = 1
    REGIONS_API_URL: str = "https://publicapi.meest.com/geo_regions"
    RAYONS_API_URL: str = "https://publicapi.meest.com/geo_districts"
    SETTLEMENTS_API_URL: str = "https://publicapi.meest.com/geo_localities"
    ADDRESSES_API_URL: str = "https://publicapi.meest.com/geo_streets"

    # Preventing DDOS on Meest API
    DELAY_TIME: int = 1

    # Meest Public API types name
    API_CITY: str = "місто"
    API_VILLAGE: str = "село"

    # ID from our db, model Region
    KYIV_ID: int = 1

    GOOGLE_CLIENT_ID: str = ""

    @staticmethod
    def configure(app):
        # Implement this method to do further configuration on your app.
        pass

    model_config = SettingsConfigDict(
        extra="allow",
        env_file=("project.env", ".env.dev", ".env"),
    )


class DevelopmentConfig(BaseConfig):
    """Development configuration."""

    DEBUG: bool = True
    ALCHEMICAL_DATABASE_URL: str


class TestingConfig(BaseConfig):
    """Testing configuration."""

    TESTING: bool = True
    PRESERVE_CONTEXT_ON_EXCEPTION: bool = False
    ALCHEMICAL_DATABASE_URL: str = "sqlite:///" + os.path.join(BASE_DIR, "database-test.sqlite3")


class ProductionConfig(BaseConfig):
    """Production configuration."""

    ALCHEMICAL_DATABASE_URL: str
    WTF_CSRF_ENABLED: bool = True


@lru_cache
def config(name: str = APP_ENV) -> DevelopmentConfig | TestingConfig | ProductionConfig:
    CONF_MAP = dict(
        development=DevelopmentConfig,
        testing=TestingConfig,
        production=ProductionConfig,
    )
    configuration = CONF_MAP[name]()
    configuration.ENV = name
    return configuration
