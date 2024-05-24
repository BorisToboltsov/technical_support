import base64

import sqlalchemy as sa
from app.models import User

from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import NoResultFound

from app import app, db


@app.route("/login", methods=["GET", "POST"])
def login():
    parameters = request.full_path
    a = parameters.index('?')
    parameters = parameters[a:]
    parameters = base64.b64decode(parameters + '==').decode("utf-8")
    if not parameters:
        return render_template("401.html"), 401
    parameters = parameters.split('&')

    parameters_dict = {}
    for parameter in parameters:
        parameter = parameter.split('=')
        parameters_dict[parameter[0]] = parameter[1]

    user_id = int(parameters_dict.get("user_id"))
    name = parameters_dict.get("name")
    telegram_id = parameters_dict.get("telegram_id")
    access = parameters_dict.get("access")

    if access == "0":
        return render_template("403.html"), 403

    if current_user.is_authenticated:
        return redirect(url_for("index"))

    query = sa.select(User).where(User.user_id == user_id)
    try:
        user = db.session.execute(query).one()[0]
    except NoResultFound:
        user = User(user_id=user_id, name=name, telegram_id=telegram_id)
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect(url_for("index"))


@app.route('/')
def index():
    return 'Hello world'
