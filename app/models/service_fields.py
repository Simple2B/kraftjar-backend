import sqlalchemy as sa

from app.database import db


field_services = sa.Table(
    "field_services",
    db.Model.metadata,
    sa.Column("service_id", sa.ForeignKey("services.id"), primary_key=True),
    sa.Column("field_id", sa.ForeignKey("fields.id"), primary_key=True),
)


class FieldService(db.Model):
    __tablename__ = "field_services"
