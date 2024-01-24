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

field_route = Blueprint("field", __name__, url_prefix="/field")


@field_route.route("/", methods=["GET"])
@login_required
def get_all():
    q = request.args.get("q", type=str, default=None)
    query = m.Field.select().order_by(m.Field.id)
    count_query = sa.select(sa.func.count()).select_from(m.Field)
    if q:
        query = (
            m.Field.select().where(m.Field.fieldname.like(f"{q}%") | m.Field.email.like(f"{q}%")).order_by(m.Field.id)
        )
        count_query = (
            sa.select(sa.func.count())
            .where(m.Field.fieldname.like(f"{q}%") | m.Field.email.like(f"{q}%"))
            .select_from(m.Field)
        )

    pagination = create_pagination(total=db.session.scalar(count_query))
    fields = list(
        db.session.execute(
            query.offset((pagination.page - 1) * pagination.per_page).limit(pagination.per_page)
        ).scalars()
    )
    return render_template(
        "field/fields.html",
        fields=fields,
        page=pagination,
        search_query=q,
    )


@field_route.route("/save", methods=["POST"])
@login_required
def save():
    form = f.FieldForm()
    if form.validate_on_submit():
        query = m.Field.select().where(m.Field.id == int(form.Field_id.data))
        u: m.Field | None = db.session.scalar(query)
        if not u:
            log(log.ERROR, "Not found field by id : [%s]", form.Field_id.data)
            flash("Cannot save field data", "danger")
            return redirect(url_for("field.get_all"))
        u.first_name = form.First_name.data
        u.last_name = form.last_name.data
        u.phone = form.phone.data
        # form.is_deleted.data is always False
        u.is_deleted = form.is_deleted.data
        u.email = form.email.data
        if form.password.data.strip("*\n "):
            u.password = form.password.data
        u.save()
        log(log.INFO, "field [%s] updated", u)
        if form.next_url.data:
            return redirect(form.next_url.data)
        return redirect(url_for("field.get_all"))

    else:
        log(log.ERROR, "field save errors: [%s]", form.errors)
        flash(f"{form.errors}", "danger")
        return redirect(url_for("field.get_all"))


@field_route.route("/delete/<int:id>", methods=["GET"])
@login_required
def delete(id: int):
    u = db.session.scalar(m.Field.select().where(m.Field.id == id))
    if not u:
        log(log.INFO, "There is no field with id: [%s]", id)
        flash("There is no such field", "danger")
        return "no field", 404

    u.is_deleted = True
    db.session.commit()
    log(log.INFO, "field deleted. field: [%s]", u)
    flash("field deleted!", "success")
    return "ok", 200
