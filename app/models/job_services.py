import sqlalchemy as sa

from app.database import db


job_services = sa.Table(
    "job_services",
    db.Model.metadata,
    sa.Column("service_id", sa.ForeignKey("services.id"), primary_key=True),
    sa.Column("job_id", sa.ForeignKey("jobs.id"), primary_key=True),
)


class JobService(db.Model):
    __tablename__ = "job_services"
