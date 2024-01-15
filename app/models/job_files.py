import sqlalchemy as sa

from app.database import db


job_files = sa.Table(
    "job_files",
    db.Model.metadata,
    sa.Column("file_id", sa.ForeignKey("files.id"), primary_key=True),
    sa.Column("job_id", sa.ForeignKey("jobs.id"), primary_key=True),
)


class JobFile(db.Model):
    __tablename__ = "job_files"
