# ruff: noqa: F401
from .auth import auth_blueprint
from .main import main_blueprint
from .admin import bp as admin_blueprint
from .user import user_route
from .field import field_route
