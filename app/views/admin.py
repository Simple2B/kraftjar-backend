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
        "admin/admins.html",
        users=users,
        page=pagination,
        search_query=q,
    )


@bp.route("/save", methods=["POST"])
@login_required
def save():
    form: f.AdminForm = f.AdminForm()
    if form.validate_on_submit():
        query = m.Admin.select().where(m.Admin.id == int(form.user_id.data))
        u: m.Admin | None = db.session.scalar(query)
        if not u:
            log(log.ERROR, "Not found admin by id : [%s]", form.user_id.data)
            flash("Cannot save admin data", "danger")
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
    form: f.NewAdminForm = f.NewAdminForm()
    if form.validate_on_submit():
        admin = m.Admin(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
        )
        log(log.INFO, "Form submitted. Admin: [%s]", admin)
        flash("Admin added!", "success")
        admin.save()
        return redirect(url_for("admin.get_all"))
    else:
        log(log.ERROR, "Admin create errors: [%s]", form.errors)
        flash(f"{form.errors}", "danger")
        return redirect(url_for("admin.get_all"))


@bp.route("/delete/<int:id>", methods=["DELETE"])
@login_required
def delete(id: int):
    u = db.session.scalar(m.Admin.select().where(m.Admin.id == id))
    if not u:
        log(log.INFO, "There is no admin with id: [%s]", id)
        flash("There is no such admin", "danger")
        return "no admin", 404

    u.is_deleted = True
    db.session.commit()
    log(log.INFO, "Admin deleted. Admin: [%s]", u)
    flash("Admin deleted!", "success")
    return "ok", 200


@bp.route("/restore/<int:id>", methods=["POST"])
@login_required
def restore(id: int):
    u = db.session.scalar(m.Admin.select().where(m.Admin.id == id))
    if not u:
        log(log.INFO, "There is no admin with id: [%s]", id)
        flash("There is no such admin", "danger")
        return "no admin", 404
    if not u.is_deleted:
        log(log.INFO, "Admin is not deleted. Admin: [%s]", u)
        flash("Admin is not deleted", "danger")
        return redirect(url_for("admin.get_all"))
    u.is_deleted = False
    db.session.commit()
    log(log.INFO, "Admin restored. Admin: [%s]", u)
    flash("Admin restored!", "success")
    return "ok", 200
