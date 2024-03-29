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

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/", methods=["GET"])
@login_required
def get_all():
    q = request.args.get("q", type=str, default=None)
    query = m.Admin.select().order_by(m.Admin.id)
    count_query = sa.select(sa.func.count()).select_from(m.Admin)
    if q:
        query = (
            m.Admin.select().where(m.Admin.username.like(f"{q}%") | m.Admin.email.like(f"{q}%")).order_by(m.Admin.id)
        )
        count_query = (
            sa.select(sa.func.count())
            .where(m.Admin.username.like(f"{q}%") | m.Admin.email.like(f"{q}%"))
            .select_from(m.Admin)
        )

    pagination = create_pagination(total=db.session.scalar(count_query))
    users = list(
        db.session.execute(
            query.offset((pagination.page - 1) * pagination.per_page).limit(pagination.per_page)
        ).scalars()
    )
    return render_template(
        "admin/users.html",
        users=users,
        page=pagination,
        search_query=q,
    )


@bp.route("/save", methods=["POST"])
@login_required
def save():
    form = f.AdminForm()
    if form.validate_on_submit():
        query = m.Admin.select().where(m.Admin.id == int(form.user_id.data))
        u: m.Admin | None = db.session.scalar(query)
        if not u:
            log(log.ERROR, "Not found user by id : [%s]", form.user_id.data)
            flash("Cannot save user data", "danger")
            return redirect(url_for("admin.get_all"))
        u.username = form.username.data
        u.email = form.email.data
        if form.password.data.strip("*\n "):
            u.password = form.password.data
        u.save()
        if form.next_url.data:
            return redirect(form.next_url.data)
        return redirect(url_for("admin.get_all"))

    else:
        log(log.ERROR, "User save errors: [%s]", form.errors)
        flash(f"{form.errors}", "danger")
        return redirect(url_for("admin.get_all"))


@bp.route("/create", methods=["POST"])
@login_required
def create():
    form = f.NewAdminForm()
    if form.validate_on_submit():
        user = m.Admin(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
        )
        log(log.INFO, "Form submitted. User: [%s]", user)
        flash("User added!", "success")
        user.save()
        return redirect(url_for("admin.get_all"))


@bp.route("/delete/<int:id>", methods=["DELETE"])
@login_required
def delete(id: int):
    u = db.session.scalar(m.Admin.select().where(m.Admin.id == id))
    if not u:
        log(log.INFO, "There is no user with id: [%s]", id)
        flash("There is no such user", "danger")
        return "no user", 404

    u.is_deleted = True
    db.session.commit()
    log(log.INFO, "User deleted. User: [%s]", u)
    flash("User deleted!", "success")
    return "ok", 200
