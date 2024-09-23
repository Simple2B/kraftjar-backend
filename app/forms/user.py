from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
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
    first_name = StringField("first_name", [DataRequired()])
    last_name = StringField("last_name", [DataRequired()])
    phone = StringField("phone", [DataRequired()])
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


class CreateUserForm(FlaskForm):
    fullname = StringField("fullname", [DataRequired()])
    first_name = StringField("first_name", [DataRequired()])
    last_name = StringField("last_name", [DataRequired()])
    phone = StringField("phone", [DataRequired()])
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
        query = m.User.select().where(m.User.fullname == field.data)
        if db.session.scalar(query) is not None:
            raise ValidationError("This username is taken.")

    def validate_phone(self, field):
        query = m.User.select().where(m.User.phone == field.data)
        if db.session.scalar(query) is not None:
            raise ValidationError("This phone number is already registered.")
