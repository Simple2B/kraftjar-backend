import sqlalchemy as sa

from app.database import db


favorite_experts = sa.Table(
    "favorite_experts",
    db.Model.metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("user_id", sa.ForeignKey("users.id")),
    sa.Column("expert_id", sa.ForeignKey("users.id")),
)
