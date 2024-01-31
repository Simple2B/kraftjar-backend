import sqlalchemy as sa
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask import current_app as app
from flask_login import login_required

from app import db
from app import forms as f
from app import models as m
from app.controllers import create_pagination
from app.logger import log
from app.utilities import Params, arg_params

service_route = Blueprint("service", __name__, url_prefix="/service")


@service_route.route("/", methods=["GET"])
@login_required
def get_all():
    q = request.args.get("q", type=str, default=None)
    stmt = sa.select(m.Service).order_by(m.Service.id)
    count_stmt = sa.select(sa.func.count()).select_from(m.Service)
    if q:
        stmt = stmt.where(m.Service.name_ua.like(f"{q}%") | m.Service.name_en.like(f"{q}%"))
        count_stmt = count_stmt.where(m.Service.name_ua.like(f"{q}%") | m.Service.name_en.like(f"{q}%"))

    pagination = create_pagination(total=db.session.scalar(count_stmt), page_size=app.config["SERVICES_PAGE_SIZE"])
    services = list(
        db.session.scalars(stmt.offset((pagination.page - 1) * pagination.per_page).limit(pagination.per_page)).all()
    )
    return render_template(
        "service/services.html",
        services=services,
        page=pagination,
        search_query=q,
    )


@service_route.route("/<uuid>/delete")
@login_required
def delete(uuid: str):
    service = db.session.scalar(m.Service.select().where(m.Service.uuid == uuid))
    if not service:
        flash("Service not found", "error")
        log(log.ERROR, "Service not found: [%s]", uuid)
        values: Params = arg_params()
        return redirect(url_for("service.get_all", **values))
    service.is_deleted = True
    db.session.commit()
    flash("Service deleted", "success")
    return redirect(url_for("service.get_all", **arg_params()))


@service_route.route("/<uuid>/restore")
@login_required
def restore(uuid: str):
    service = db.session.scalar(m.Service.select().where(m.Service.uuid == uuid))
    if not service:
        flash("Service not found", "error")
        log(log.ERROR, "Service not found: [%s]", uuid)
        values: Params = arg_params()
        return redirect(url_for("service.get_all", **values))
    service.is_deleted = False
    db.session.commit()
    flash("Service restored", "success")
    return redirect(url_for("service.get_all", **arg_params()))


@service_route.route("/<uuid>/edit", methods=["GET", "POST"])
@login_required
def edit(uuid: str):
    service: m.Service = db.session.scalar(m.Service.select().where(m.Service.uuid == uuid))
    if not service:
        flash("Service not found", "error")
        log(log.ERROR, "Service not found: [%s]", uuid)
        return redirect(url_for("service.get_all", **arg_params()))

    form: f.ServiceForm = f.ServiceForm()
    if form.validate_on_submit():
        service.name_ua = form.name_ua.data
        service.name_en = form.name_en.data
        db.session.commit()
        flash("Service updated", "success")
        return redirect(url_for("service.get_all", **arg_params()))
    elif form.is_submitted():
        # flash("Form validation error", "error")
        log(log.ERROR, "Form validation error: [%s]", form.errors)

    form.name_ua.data = service.name_ua
    form.name_en.data = service.name_en
    form.parent_id.data = str(service.parent_id)
    form.id.data = str(service.id)
    form.uuid.data = service.uuid
    form.parent_uuid.data = service.parent.uuid if service.parent else None

    return render_template("service/edit.html", form=form, service=service)
