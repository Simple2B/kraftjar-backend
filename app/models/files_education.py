import sqlalchemy as sa

from app.database import db


files_education = sa.Table(
    "files_education",
    db.Model.metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column(
        "file_id",
        sa.ForeignKey("files.id"),
    ),
    sa.Column(
        "education_id",
        sa.ForeignKey("educations.id"),
    ),
)
