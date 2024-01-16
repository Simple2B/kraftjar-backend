import sqlalchemy as sa

from app.database import db


user_locations = sa.Table(
    "user_locations",
    db.Model.metadata,
    sa.Column("user_id", sa.ForeignKey("users.id"), primary_key=True),
    sa.Column("location_id", sa.ForeignKey("locations.id"), primary_key=True),
)


class UserLocation(db.Model):
    __tablename__ = "user_locations"
