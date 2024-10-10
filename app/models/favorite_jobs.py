import sqlalchemy as sa

from app.database import db


favorite_jobs = sa.Table(
    "favorite_jobs",
    db.Model.metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("user_id", sa.ForeignKey("users.id")),
    sa.Column("job_id", sa.ForeignKey("jobs.id")),
)
