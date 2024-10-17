import sqlalchemy as sa

from app.database import db

notification_devices = sa.Table(
    "notification_devices",
    db.Model.metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("notification_id", sa.ForeignKey("push_notifications.id")),
    sa.Column("device_id", sa.ForeignKey("devices.id")),
)
