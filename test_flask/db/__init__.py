from typing import Generator

from faker import Faker
from sqlalchemy import func

from app import db
from app import models as m

faker = Faker()

NUM_TEST_USERS = 100


def gen_test_items(num_objects: int) -> Generator[tuple[str, str], None, None]:
    from faker import Faker

    fake = Faker()

    DOMAINS = ("com", "com.br", "net", "net.br", "org", "org.br", "gov", "gov.br")

    i = db.session.query(func.max(m.Admin.id)).scalar()

    for _ in range(num_objects):
        i += 1
        # Primary name
        fullname = fake.first_name()

        company = fake.company().split()[0].strip(",")

        # Company DNS
        dns_org = fake.random_choices(elements=DOMAINS, length=1)[0]

        # email formatting
        yield f"{fullname}{i}".lower(), f"{fullname}{i}@{company}.{dns_org}".lower()


def populate(count: int = NUM_TEST_USERS):
    for username, email in gen_test_items(count):
        m.Admin(username=username, email=email, password_hash="*").save(False)

    db.session.commit()
