from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import models as m
from app.logger import log
from config import config

CFG = config()


def update_user_average_rate(user: m.User, db: Session):
    """Update user average rate"""
    stmt = sa.select(m.Rate).where(m.Rate.receiver_id == user.id)
    rates = db.scalars(stmt).all()

    if not rates:
        return

    total_rate = 0
    for rate in rates:
        total_rate += rate.rate

    average_rate = total_rate / len(rates)

    stmt_update = (
        sa.update(m.User)
        .where(m.User.id == user.id)
        .values(average_rate=average_rate)
        .execution_options(synchronize_session="fetch")
    )
    db.execute(stmt_update)
    db.flush()
    log(log.DEBUG, "User %s average rate updated to %s", user.id, average_rate)


def update_users_average_rate(users: Sequence[m.User], db: Session):
    """Update users average rate"""
    for user in users:
        update_user_average_rate(user, db)
    return
