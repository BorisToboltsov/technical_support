from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    IntegerField,
)
from wtforms.validators import DataRequired, Length, NumberRange


class LoginForm(FlaskForm):
    username = StringField("Логин", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember_me = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")


class PostForm(FlaskForm):
    post = TextAreaField(
        "Новый комментарий", validators=[DataRequired(), Length(min=1, max=300)]
    )
    add = SubmitField("Добавить")


class SelectStatusForm(FlaskForm):
    select = SelectField("Выбор статуса", choices=[])
    change = SubmitField("Изменить")

    def set_choices(self, select_list):
        self.select.choices = select_list


class SelectUserForm(FlaskForm):
    select = SelectField("Выбор исполнителя", choices=[])

    def set_choices(self, select_list):
        self.select.choices = select_list


class AppealTextForm(FlaskForm):
    select = SelectField("Выбор филиала", choices=[])
    post = TextAreaField(
        "Текст обращения", validators=[DataRequired(), Length(min=1, max=500)]
    )
    cabinet_number = IntegerField("№ кабинета", validators=[DataRequired(), NumberRange(min=1, max=2000)])
    add = SubmitField("Добавить")

    def set_choices(self, select_list):
        self.select.choices = select_list
