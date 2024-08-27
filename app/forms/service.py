import sqlalchemy as sa
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Optional
from wtforms_sqlalchemy.fields import QuerySelectField

from app import db
from app import models as m


class ServiceForm(FlaskForm):
    name_ua = StringField("Name UA", validators=[DataRequired(), Length(3, 128)])
    name_en = StringField("Name EN", validators=[DataRequired(), Length(3, 128)])
    parent_id = QuerySelectField(
        "Parent ID",
        query_factory=lambda: db.session.scalars(sa.select(m.Service)).all(),
        get_label="name_ua",
        allow_blank=True,
    )
    save = SubmitField("Save")

    def validate_name_ua(self, field):
        query = m.Service.select().where(m.Service.name_ua == field.data)
        if db.session.scalar(query) is not None:
            raise ValidationError("This name_ua is taken.")

    def validate_name_en(self, field):
        query = m.Service.select().where(m.Service.name_en == field.data)
        if db.session.scalar(query) is not None:
            raise ValidationError("This name_en is already registered.")

    def validate_parent_id(self, field):
        if not field.data or field.data == "0":  # Дозволяємо порожнє значення або '0'
            return
        stmt = m.Service.select().where(m.Service.id == int(field.data.id))
        if db.session.scalar(stmt) is None:
            raise ValidationError("This parent_id does not exist.")


class EditServiceForm(FlaskForm):
    service_uuid = StringField("ID", validators=[DataRequired()])
    name_ua = StringField("Name UA", validators=[DataRequired(), Length(3, 128)])
    name_en = StringField("Name EN", validators=[DataRequired(), Length(3, 128)])
    parent_id = StringField("parent_id", validators=[Optional()])
    save = SubmitField("Save")

    def validate_name_ua(self, field):
        query = (
            m.Service.select().where(m.Service.name_ua == field.data).where(m.Service.uuid != self.service_uuid.data)
        )
        if db.session.scalar(query) is not None:
            raise ValidationError("This name_ua is taken.")

    def validate_name_en(self, field):
        query = (
            m.Service.select().where(m.Service.name_en == field.data).where(m.Service.uuid != self.service_uuid.data)
        )
        if db.session.scalar(query) is not None:
            raise ValidationError("This name_en is already registered.")

    def validate_parent_id(self, field):
        if not field.data or field.data == "0":
            return
        stmt = m.Service.select().where(m.Service.uuid == self.service_uuid.data)
        stmt2 = m.Service.select().where(m.Service.id == int(field.data))
        if db.session.scalar(stmt) and db.session.scalar(stmt2) is None:
            raise ValidationError("This parent_id does not exist.")
