import sqlalchemy as sa

from app.database import db


job_rates = sa.Table(
    "job_rates",
    db.Model.metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("rate_id", sa.ForeignKey("rates.id")),
    sa.Column("job_id", sa.ForeignKey("jobs.id")),
)


class JobRate(db.Model):
    __tablename__ = "job_rates"
