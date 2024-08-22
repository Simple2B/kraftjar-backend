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


class AdminForm(FlaskForm):
    next_url = StringField("next_url")
    user_id = StringField("user_id", [DataRequired()])
    username = StringField("username", [DataRequired()])
    email = StringField("email", [DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(6, 30)])
    password_confirmation = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Password do not match."),
        ],
    )
    submit = SubmitField("Save")

    def validate_username(self, field):
        query = m.Admin.select().where(m.Admin.username == field.data).where(m.Admin.id != int(self.user_id.data))
        if db.session.scalar(query) is not None:
            raise ValidationError("This username is taken.")

    def validate_email(self, field):
        query = m.Admin.select().where(m.Admin.email == field.data).where(m.Admin.id != int(self.user_id.data))
        if db.session.scalar(query) is not None:
            raise ValidationError("This email is already registered.")


class NewAdminForm(FlaskForm):
    email = StringField("email", [DataRequired(), Email()])
    username = StringField("Username", [DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), Length(6, 30)])
    password_confirmation = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Password do not match."),
        ],
    )
    submit = SubmitField("Save")

    def validate_username(self, field):
        query = m.Admin.select().where(m.Admin.username == field.data)
        if db.session.scalar(query) is not None:
            raise ValidationError("This username is taken.")

    def validate_email(self, field):
        query = m.Admin.select().where(m.Admin.email == field.data)
        if db.session.scalar(query) is not None:
            raise ValidationError("This email is already registered.")
