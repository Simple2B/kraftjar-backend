import sqlalchemy as sa

from app.database import db


user_professions = sa.Table(
    "user_professions",
    db.Model.metadata,
    sa.Column("user_id", sa.ForeignKey("users.id"), primary_key=True),
    sa.Column("profession_id", sa.ForeignKey("professions.id"), primary_key=True),
)


class UserProfession(db.Model):
    __tablename__ = "user_professions"
