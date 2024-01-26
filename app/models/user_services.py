import sqlalchemy as sa

from app.database import db


user_services = sa.Table(
    "user_services",
    db.Model.metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("user_id", sa.ForeignKey("users.id")),
    sa.Column("service_id", sa.ForeignKey("services.id")),
)
