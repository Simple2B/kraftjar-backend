from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    ValidationError,
)
from wtforms.validators import DataRequired, Email, Length, EqualTo

from app import models as m
from app import db


class UserForm(FlaskForm):
    next_url = StringField("next_url")
    user_id = StringField("user_id", [DataRequired()])
    email = StringField("email", [DataRequired(), Email()])
    fullname = StringField("fullname", [DataRequired()])
    phone = StringField("phone", [DataRequired()])
    is_deleted = BooleanField("is_deleted", [DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), Length(6, 30)])
    password_confirmation = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Password do not match."),
        ],
    )
    submit = SubmitField("Save")

    def validate_fullname(self, field):
        query = m.User.select().where(m.User.fullname == field.data).where(m.User.id != int(self.user_id.data))
        if db.session.scalar(query) is not None:
            raise ValidationError("This username is taken.")

    def validate_email(self, field):
        query = m.User.select().where(m.User.email == field.data).where(m.User.id != int(self.user_id.data))
        if db.session.scalar(query) is not None:
            raise ValidationError("This email is already registered.")
