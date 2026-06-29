from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField,
    IntegerField, FloatField, TextAreaField, SelectField,
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo,
    NumberRange, Optional, ValidationError,
)
from app.models import User


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Register")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Username already taken.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Email already registered.")


class VehicleForm(FlaskForm):
    name = StringField("Make", validators=[DataRequired(), Length(max=120)])
    model = StringField("Model", validators=[DataRequired(), Length(max=120)])
    year = IntegerField("Year", validators=[DataRequired(), NumberRange(min=1900, max=2100)])
    category = SelectField(
        "Category",
        choices=[
            ("sedan", "Sedan"),
            ("suv", "SUV"),
            ("truck", "Truck"),
            ("van", "Van"),
            ("sports", "Sports"),
            ("electric", "Electric"),
        ],
        validators=[DataRequired()],
    )
    price = FloatField("Price (USD)", validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField("Stock quantity", validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Save vehicle")


class OrderForm(FlaskForm):
    quantity = IntegerField(
        "Quantity",
        validators=[DataRequired(), NumberRange(min=1, max=100)],
    )
    submit = SubmitField("Place order")


class UpdateOrderStatusForm(FlaskForm):
    status = SelectField(
        "Status",
        choices=[
            ("pending", "Pending"),
            ("confirmed", "Confirmed"),
            ("in_production", "In production"),
            ("shipped", "Shipped"),
            ("delivered", "Delivered"),
            ("cancelled", "Cancelled"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Update status")
