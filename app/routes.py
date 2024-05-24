import base64

import sqlalchemy as sa
from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import NoResultFound

from app import app, db
from app.forms import SelectUserForm, SelectStatusForm
from app.models import User, Status, UserRequest


@app.route("/login", methods=["GET", "POST"])
def login():
    parameters = request.full_path
    a = parameters.index("?")
    parameters = parameters[a:]
    parameters = base64.b64decode(parameters + "==").decode("utf-8")
    if not parameters:
        return render_template("401.html"), 401
    parameters = parameters.split("&")

    parameters_dict = {}
    for parameter in parameters:
        parameter = parameter.split("=")
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


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/")
@app.route("/index")
def index():
    obj_status_list = Status.query.all()
    status_list = [status.name for status in obj_status_list]
    status_list.append('Все')
    status_form = SelectStatusForm()
    status_form.set_choices(status_list)
    status_form.select.default = 'Новое'
    status_form.process()

    obj_user_list = User.query.all()
    user_list = [user.name for user in obj_user_list]

    user_list.append('Все')
    user_form = SelectUserForm()
    user_form.set_choices(user_list)
    user_form.select.default = 'Все'
    user_form.process()

    return render_template("index.html", title="Техническая поддержка",
                           status_form=status_form,
                           user_form=user_form)


@app.route("/api/data")
def data():
    query = UserRequest.query

    # search filter
    application_number = request.args.get('application_number')
    user_fio = request.args.get('user_fio')
    status = request.args.get('status')
    user = request.args.get('user')
    datepicker_min = request.args.get('datepicker_min')
    datepicker_max = request.args.get('datepicker_max')

    if status == 'Все':
        pass
    else:
        query = query.join(Status).filter(sa.func.lower(Status.name) == status.lower())
    if user == 'Все':
        pass
    else:
        query = query.join(User, onclause=(User.id == UserRequest.executor_id)).filter(sa.func.lower(User.name) == user.lower())

    if application_number:
        try:
            query = query.filter(UserRequest.id == int(application_number))
        except ValueError:
            pass
    if user_fio:
        try:
            query = query.filter(UserRequest.user.has(sa.func.lower(User.name).like(f"%{user_fio.lower()}%")))
        except ValueError:
            pass
    if datepicker_min:
        if datepicker_max:
            query = query.filter(UserRequest.created_at.between(datepicker_min, f'{datepicker_max} 23:59:59.999'))
        else:
            query = query.filter(UserRequest.created_at >= datepicker_min)

    if datepicker_max:
        if datepicker_min:
            query = query.filter(UserRequest.created_at.between(datepicker_min, f'{datepicker_max} 23:59:59.999'))
        else:
            query = query.filter(UserRequest.created_at <= datepicker_max)

    total_filtered = query.count()

    # sorting
    order = []
    i = 0
    while True:
        col_index = request.args.get(f"order[{i}][column]")
        if col_index is None:
            break
        col_name = request.args.get(f"columns[{col_index}][data]")
        # if col_name not in ['created_at', 'status.name']:
        col_name = "id"
        descending = request.args.get(f"order[{i}][dir]") == "asc"
        col_id = getattr(UserRequest, col_name)
        if descending:
            col_id = col_id.desc()
        order.append(col_id)
        i += 1
    if order:
        query = query.order_by(*order)

    # pagination
    start = request.args.get("start", type=int)
    length = request.args.get("length", type=int)
    query = query.offset(start).limit(length)

    appeal_list = []
    for i, appeal in enumerate(query, 1):
        entity = appeal.to_dict()
        entity["number"] = i
        appeal_list.append(entity)

    obj_status_list = Status.query.all()
    status_list = [status.name for status in obj_status_list]

    priority_theme = 'Звонок'
    sorted_appeal_list = sorted(appeal_list, key=lambda x: (x['theme'] != priority_theme))

    return {
        "data": sorted_appeal_list,
        "recordsFiltered": total_filtered,
        "recordsTotal": UserRequest.query.count(),
        "draw": request.args.get("draw", type=int),
        "status": status_list,
    }


@app.route("/statistics")
@login_required
def statistics():
    query = UserRequest.query
    total_user_request = query.all()
    status_list = Status.query.all()
    total_status_list = []
    for status in status_list:
        user_request = query.filter(UserRequest.status.has(name=status.name))
        total_status_request = user_request.count()
        total_status_list.append({'status': status, 'total': total_status_request})

    return render_template("statistics.html", title="Техническая поддержка",
                           total_status_list=total_status_list,
                           total_user_request=len(total_user_request))


@app.route("/api/statistics")
@login_required
def statistics_data():
    users_query = (sa.select(User.name, Status.name, sa.func.count()).
                   join(UserRequest, User.id == UserRequest.executor_id).
                   join(Status, Status.id == UserRequest.status_id).
                   group_by(User.name, Status.name))
    users_query_list = db.session.execute(users_query).all()

    data_list = []
    for user_query in users_query_list:
        k = True
        for data in data_list:
            if user_query[0] == data['fio']:
                data.update({user_query[1]: user_query[2]})
                k = False
        if k:
            data_list.append({'fio': user_query[0], user_query[1]: user_query[2]})

    return {
        "data": data_list,
        "recordsFiltered": len(data_list),
        "recordsTotal": len(data_list),
        "draw": request.args.get("draw", type=int),
    }
