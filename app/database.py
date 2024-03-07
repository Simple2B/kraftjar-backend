from typing import Generator

import sqlalchemy
from sqlalchemy.orm import Session

from config import config

CFG = config()

if CFG.IS_API:
    from alchemical import Alchemical
else:
    from alchemical.flask import Alchemical

db = Alchemical()

if CFG.IS_API:
    db.initialize(url=CFG.ALCHEMICAL_DATABASE_URL)


def get_db() -> Generator[Session, None, None]:
    with db.Session() as session:

        @sqlalchemy.event.listens_for(session, "connect")
        def on_connect(dbapi_connection, connection_record):
            dbapi_connection.create_function("lower", 1, lambda arg: arg.lower())

        yield session
