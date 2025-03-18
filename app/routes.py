import base64
import os
from datetime import datetime

import sqlalchemy as sa
from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import NoResultFound

from app import app, db
from app.forms import SelectUserForm, SelectStatusForm, PostForm, AppealTextForm, SelectThemeForm
from app.mail import send_email
from app.models import User, Status, UserRequest, UserRequestHistory, Comment, Branch, Theme
from openproject.database.work_packages import ApiWorkPackages


@app.route("/technical/login", methods=["GET", "POST"])
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
    phone = parameters_dict.get("phone")
    is_edited = True if parameters_dict.get("is_edited") == "1" else False

    try:
        telegram_id = int(telegram_id)
        phone = int(phone)
        is_edited = int(is_edited)
    except ValueError:
        telegram_id = 0
        phone = 0
        is_edited = 0

    if access == "0":
        return render_template("403.html"), 403

    if current_user.is_authenticated:
        return redirect(url_for("index"))

    query = sa.select(User).where(User.user_id == user_id)
    try:
        user = db.session.execute(query).one()[0]
        if user.is_edited != int(is_edited) or user.phone != int(phone) or user.telegram_id != int(telegram_id) or user.name != name:
            user.is_edited = int(is_edited)
            user.phone = int(phone)
            user.telegram_id = telegram_id
            user.name = name
            db.session.add(user)
            db.session.commit()
    except NoResultFound:
        user = User(user_id=user_id, name=name, telegram_id=telegram_id, phone=phone, is_edited=is_edited)
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect(url_for("index"))


@app.route("/technical/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/technical/appeal_list")
@login_required
def appeal_list():
    obj_status_list = Status.query.all()
    status_list = [status.name for status in obj_status_list]
    status_list.append('Все')
    status_form = SelectStatusForm()
    status_form.set_choices(status_list)
    status_form.select.default = 'Новое'
    status_form.process()

    obj_user_list = User.query.filter(User.is_edited == True)
    user_list = [user.name for user in obj_user_list]

    user_list.append('Все')
    user_form = SelectUserForm()
    user_form.set_choices(user_list)
    user_form.select.default = 'Все'
    user_form.process()

    obj_theme_list = Theme.query.all()
    theme_list = [status.name for status in obj_theme_list]
    theme_list.append('Все')
    theme_form = SelectThemeForm()
    theme_form.set_choices(theme_list)
    theme_form.select.default = 'Все'
    theme_form.process()

    return render_template("appeal_list.html", title="Техническая поддержка",
                           status_form=status_form,
                           user_form=user_form,
                           theme_form=theme_form)


@app.route("/technical/api/data")
@login_required
def data():
    query = UserRequest.query

    # search filter
    application_number = request.args.get('application_number')
    user_fio = request.args.get('user_fio')
    status = request.args.get('status')
    theme = request.args.get('theme')
    created_me = request.args.get('created_me')
    user = request.args.get('user')
    datepicker_min = request.args.get('datepicker_min')
    datepicker_max = request.args.get('datepicker_max')
    if created_me == 'true':
        query = query.join(User, onclause=(User.id == UserRequest.user_id)).filter(sa.func.lower(User.name) == current_user.name.lower())
    if status == 'Все':
        pass
    else:
        query = query.join(Status).filter(sa.func.lower(Status.name) == status.lower())
    if theme == 'Все':
        pass
    else:
        query = query.join(Theme).filter(sa.func.lower(Theme.name) == theme.lower())
    if user == 'Все':
        pass
    else:
        if status:
            query = query.filter(UserRequest.executor.has(name=user))
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


@app.route("/technical/statistics")
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


@app.route("/technical/api/statistics")
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


@app.route("/technical/appeal/id=<appeal_id>", methods=["GET", "POST"])
@login_required
def appeal_handler(appeal_id):
    appeal = db.first_or_404(
        sa.select(UserRequest).where(UserRequest.id == int(appeal_id))
    )
    if appeal.executor is None and current_user.is_edited:
        appeal.executor = current_user
        query = sa.select(Status).where(Status.name == "В работе")
        status = db.session.execute(query).one()[0]
        appeal.status = status
        history = UserRequestHistory(
            executor_id=current_user.id, status=status, user_request=appeal
        )
        db.session.add(history)
        db.session.commit()

    obj_list = Status.query.all()
    status_list = [status.name for status in obj_list]
    status_form = SelectStatusForm()
    status_form.set_choices(status_list)
    status_form.select.default = appeal.status.name

    if status_form.is_submitted() and status_form.select.data:
        new_status = None
        for status in obj_list:
            if status.name == status_form.select.data:
                new_status = status
        appeal.status = new_status
        if new_status.name == 'Завершено':
            appeal.closed_at = datetime.now()
            appeal.executor_id = current_user.id
        db.session.add(appeal)

        history = UserRequestHistory(
            executor_id=current_user.id, status=new_status, user_request=appeal
        )
        db.session.add(history)

        db.session.commit()
        return redirect(f"/technical/appeal/id={appeal_id}")
    status_form.process()

    form = PostForm()
    if form.validate_on_submit() and form.post.data:
        post = Comment(
            text=form.post.data,
            executor_id=current_user.id,
            user_request_id=appeal.id,
        )
        db.session.add(post)
        db.session.commit()
        return redirect(f"/technical/appeal/id={appeal_id}")

    query = Comment.query
    comments = query.filter(Comment.user_request.has(id=appeal.id)).order_by(
        Comment.created_at.desc()
    )

    history_query = UserRequestHistory.query
    history_list = history_query.filter(
        UserRequestHistory.user_request.has(id=appeal.id)
    ).order_by(UserRequestHistory.created_at.desc())

    return render_template(
        "appeal.html",
        appeal=appeal,
        comments=comments,
        form=form,
        status_form=status_form,
        status_list=status_list,
        history_list=history_list,
        current_user=current_user,
    )


@app.route("/technical/", methods=["GET", "POST"])
@app.route("/technical/index", methods=["GET", "POST"])
@login_required
def index():
    form = AppealTextForm()
    branch_query = Branch.query.all()
    branch_list = [branch.name for branch in branch_query]
    form.set_choices(branch_list)

    theme_query = Theme.query.all()
    theme_list = [theme.name for theme in theme_query]
    theme_list_sort = sorted(theme_list, key=len, reverse=True)
    form.set_choices_theme(theme_list_sort)

    if form.validate_on_submit() and form.post.data:
        query = sa.select(Status).where(sa.func.lower(Status.name) == "Новое".lower())
        status = db.session.execute(query).one()[0]

        user_request = UserRequest(
            text=form.post.data,
            user=current_user,
            status=status,
            cabinet_number=form.cabinet_number.data,
            channel='Сайт',
        )

        new_theme = None
        for theme in theme_query:
            if theme.name == form.select_theme.data:
                new_theme = theme
        user_request.theme = new_theme

        new_branch = None
        for branch in branch_query:
            if branch.name == form.select.data:
                new_branch = branch
        user_request.branch = new_branch

        description = f"""ФИО: {current_user.name}
Телефон: {current_user.phone}
Филиал: {user_request.branch.name}
Кабинет: {user_request.cabinet_number}

Тема: {user_request.theme.name}
Описание: {user_request.text}"""

        if user_request.theme.name != 'Компьютер/Принтер/ПО':
            work_packages = ApiWorkPackages()
            work_packages.save_work_packages(user_request.theme.name, description)

            query = sa.select(Status).where(sa.func.lower(Status.name) == "Передано в OP".lower())
            status = db.session.execute(query).one()[0]
            user_request.status = status
        elif user_request.theme.name == 'Компьютер/Принтер/ПО':
            send_email('Золотая пора, заявка в техподдержку.', [os.environ.get("RECIPIENT")], description)

        db.session.add(user_request)
        db.session.flush()

        request_user_history = UserRequestHistory(executor=None,
                                                  status=status,
                                                  user_request=user_request)
        db.session.add(request_user_history)

        db.session.commit()
        return render_template("accept_request.html")
    return render_template("create_request.html",
                           form=form,)
