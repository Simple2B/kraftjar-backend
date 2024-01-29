import sqlalchemy as sa

from app.database import db

user_locations = sa.Table(
    "user_locations",
    db.Model.metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("user_id", sa.ForeignKey("users.id")),
    sa.Column("location_id", sa.ForeignKey("locations.id")),
)
