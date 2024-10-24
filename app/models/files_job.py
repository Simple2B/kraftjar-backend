import sqlalchemy as sa

from app.database import db


files_job = sa.Table(
    "files_job",
    db.Model.metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column(
        "file_id",
        sa.ForeignKey("files.id"),
    ),
    sa.Column(
        "job_id",
        sa.ForeignKey("jobs.id"),
    ),
)
