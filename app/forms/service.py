from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError, HiddenField
from wtforms.validators import DataRequired, Length

from app import models as m
from app import db


class ServiceForm(FlaskForm):
    name_ua = StringField("Name UA", validators=[DataRequired(), Length(3, 128)])
    name_en = StringField("Name EN", validators=[DataRequired(), Length(3, 128)])
    parent_id = StringField("Parent ID", validators=[DataRequired()])

    id = HiddenField("ID")

    save = SubmitField("Save")

    def validate_parent_id(self, field):
        if field.data == 0:
            return
        stmt = m.Service.select().where(m.Service.id == field.data)
        service: m.Service | None = db.session.scalar(stmt)
        if service is None:
            raise ValidationError("This parent_id is not exist.")

        if service.id == int(self.id.data):
            raise ValidationError("Parent_id refers to to itself.")
