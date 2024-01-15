from pydantic import BaseModel


class TestUser(BaseModel):
    __test__ = False

    first_name: str
    last_name: str

    phone: str
    email: str
    password: str


class TestData(BaseModel):
    __test__ = False

    test_users: list[TestUser]
