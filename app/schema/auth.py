# Authorization schema
from pydantic import BaseModel


class Auth(BaseModel):
    phone: str
    password: str
