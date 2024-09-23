import sqlalchemy as sa
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required

from app import db
from app import forms as f
from app import models as m
from app.controllers import create_pagination
from app.logger import log

user_route = Blueprint("user", __name__, url_prefix="/user")


@user_route.route("/", methods=["GET"])
@login_required
def get_all():
    search_query = request.args.get("q", type=str, default=None)
    query = m.User.select().order_by(m.User.id)
    count_query = sa.select(sa.func.count()).select_from(m.User)

    if search_query:
        query = (
            m.User.select()
            .where(m.User.fullname.like(f"{search_query}%") | m.User.phone.like(f"{search_query}%"))
            .order_by(m.User.id)
        )
        count_query = (
            sa.select(sa.func.count())
            .where(m.User.fullname.like(f"{search_query}%") | m.User.phone.like(f"{search_query}%"))
            .select_from(m.User)
        )

    pagination = create_pagination(total=db.session.scalar(count_query))
    users = list(
        db.session.execute(
            query.offset((pagination.page - 1) * pagination.per_page).limit(pagination.per_page)
        ).scalars()
    )

    return render_template(
        "user/users.html",
        users=users,
        page=pagination,
        search_query=search_query,
    )


@user_route.route("/save", methods=["POST"])
@login_required
def save():
    form = f.UserForm()
    if form.validate_on_submit():
        query = m.User.select().where(m.User.id == int(form.user_id.data))
        u: m.User | None = db.session.scalar(query)
        if not u:
            log(log.ERROR, "Not found user by id : [%s]", form.user_id.data)
            flash("Cannot save user data", "danger")
            return redirect(url_for("user.get_all"))
        u.fullname = form.fullname.data.strip()
        u.first_name = form.first_name.data.strip()
        u.last_name = form.last_name.data.strip()
        u.phone = form.phone.data.strip()
        # form.is_deleted.data is always False
        u.email = form.email.data.strip()
        if form.password.data.strip("*\n "):
            u.password = form.password.data
        u.save()
        log(log.INFO, "User [%s] updated", u)
        if form.next_url.data:
            return redirect(form.next_url.data)
        return redirect(url_for("user.get_all"))

    else:
        log(log.ERROR, "User save errors: [%s]", form.errors)
        flash(f"{form.errors}", "danger")
        return redirect(url_for("user.get_all"))


@user_route.route("/delete/<int:id>", methods=["DELETE"])
@login_required
def delete(id: int):
    u = db.session.scalar(m.User.select().where(m.User.id == id))
    if not u:
        log(log.INFO, "There is no user with id: [%s]", id)
        flash("There is no such user", "danger")
        return "no user", 404

    u.is_deleted = True
    db.session.commit()
    log(log.INFO, "User deleted. User: [%s]", u)
    flash("User deleted!", "success")
    return "ok", 200


@user_route.route("/create", methods=["POST"])
@login_required
def create():
    form: f.CreateUserForm = f.CreateUserForm()
    if form.validate_on_submit():
        u = m.User(
            fullname=form.fullname.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            email=form.email.data,
            password=form.password.data,
        )
        u.save()
        log(log.INFO, "User [%s] created", u)
        return redirect(url_for("user.get_all"))

    else:
        log(log.ERROR, "User create errors: [%s]", form.errors)
        flash(f"{form.errors}", "danger")
        return redirect(url_for("user.get_all"))
