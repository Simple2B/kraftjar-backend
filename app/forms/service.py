from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError, HiddenField
from wtforms.validators import DataRequired, Length

from app import models as m
from app import db


class ServiceForm(FlaskForm):
    name_ua = StringField("Name UA", validators=[DataRequired(), Length(3, 128)])
    name_en = StringField("Name EN", validators=[DataRequired(), Length(3, 128)])
    parent_id = HiddenField("Parent ID", validators=[DataRequired()])
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
        if field.data == 0:
            return
        stmt = m.Service.select().where(m.Service.id == field.data)
        if db.session.scalar(stmt) is None:
            raise ValidationError("This parent_id is not exist.")
