from app import db
import sqlalchemy as sa
from app import models as m
from api.controllers import update_user_average_rate


def fix_users_average_rate():
    """Update users average rate"""
    with db.begin() as session:
        stmt = sa.select(m.User)
        users = session.scalars(stmt).all()

        for user in users:
            update_user_average_rate(user, session)
