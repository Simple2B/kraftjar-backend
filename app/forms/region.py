from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length

from app import db
from app import models as m


class RegionForm(FlaskForm):
    region_id = StringField("Region ID", validators=[DataRequired(), Length(3, 128)])
    name_ua = StringField("Name UA", validators=[DataRequired(), Length(3, 128)])
    name_en = StringField("Name EN", validators=[DataRequired(), Length(3, 128)])
    save = SubmitField("Save")

    def validate_name_ua(self, field):
        query = m.Region.select().where(m.Region.name_ua == field.data)
        if db.session.scalar(query) is not None:
            raise ValidationError("This name_ua is taken.")

    def validate_name_en(self, field):
        query = m.Region.select().where(m.Region.name_en == field.data)
        if db.session.scalar(query) is not None:
            raise ValidationError("This name_en is already registered.")
