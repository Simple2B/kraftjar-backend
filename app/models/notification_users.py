import sqlalchemy as sa

from app.database import db

notification_users = sa.Table(
    "notification_users",
    db.Model.metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("notification_id", sa.ForeignKey("push_notifications.id")),
    sa.Column("user_id", sa.ForeignKey("users.id")),
)