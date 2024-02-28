import sqlalchemy as sa

from app.database import db


saved_jobs = sa.Table(
    "saved_jobs",
    db.Model.metadata,
    sa.Column("user_id", sa.ForeignKey("users.id"), primary_key=True),
    sa.Column("job_id", sa.ForeignKey("jobs.id"), primary_key=True),
)


class SavedJob(db.Model):
    __tablename__ = "saved_jobs"
