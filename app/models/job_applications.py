import sqlalchemy as sa

from app.database import db


job_applications = sa.Table(
    "job_applications",
    db.Model.metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("application_id", sa.ForeignKey("applications.id")),
    sa.Column("job_id", sa.ForeignKey("jobs.id")),
)
