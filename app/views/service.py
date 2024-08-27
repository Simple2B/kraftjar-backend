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
from app.utilities import arg_params, Params

service_route = Blueprint("service", __name__, url_prefix="/service")


@service_route.route("/", methods=["GET"])
@login_required
def get_all():
    q = request.args.get("q", type=str, default=None)
    query = m.Service.select().order_by(m.Service.id)
    count_query = sa.select(sa.func.count()).select_from(m.Service)
    if q:
        query = (
            m.Service.select()
            .where(m.Service.name_ua.ilike(f"{q}%") | m.Service.name_en.ilike(f"{q}%"))
            .order_by(m.Service.id)
        )
        count_query = (
            sa.select(sa.func.count())
            .where(m.Service.name_ua.ilike(f"{q}%") | m.Service.name_en.ilike(f"{q}%"))
            .select_from(m.Service)
        )

    pagination = create_pagination(total=db.session.scalar(count_query))
    services = list(
        db.session.execute(
            query.offset((pagination.page - 1) * pagination.per_page).limit(pagination.per_page)
        ).scalars()
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
    link = request.referrer
    if not link:
        link = url_for("service.get_all", **arg_params())
    if not service:
        flash("Service not found", "error")
        values: Params = arg_params()
        log(log.ERROR, "Service not found: [%s]", uuid)
        return redirect(url_for("service.get_all", **values))
    service.is_deleted = True
    db.session.commit()
    flash("Service deleted", "success")
    return redirect(link)


@service_route.route("/<uuid>/edit", methods=["GET", "POST"])
@login_required
def edit(uuid: str):
    service: m.Service = db.session.scalar(m.Service.select().where(m.Service.uuid == uuid))
    parents: m.Service = db.session.scalars(m.Service.select().where(m.Service.uuid != uuid)).all()
    if not service:
        flash("Service not found", "error")
        log(log.ERROR, "Service not found: [%s]", uuid)
        return redirect(url_for("service.get_all", **arg_params()))

    form: f.EditServiceForm = f.EditServiceForm()

    if form.validate_on_submit():
        service.name_ua = form.name_ua.data.strip()
        service.name_en = form.name_en.data.strip()

        if form.parent_id.data:
            parent = db.session.scalar(sa.select(m.Service).where(m.Service.id == form.parent_id.data))
            if not parent:
                flash("Parent not found", "error")
                log(log.ERROR, "Parent not found: [%s]", form.parent_id.data)
                return redirect(url_for("service.get_all", **arg_params()))
            service.parent_id = form.parent_id.data
        else:
            service.parent_id = None

        db.session.commit()
        flash("Service updated", "success")
        log(log.INFO, "Service updated: [%s]", service)
        return redirect(url_for("service.get_all", **arg_params()))

    elif form.is_submitted():
        flash(f"Form validation error {form.errors}", "danger")
        log(log.ERROR, "Form validation error: [%s]", form.errors)

    if not form.is_submitted():
        form.service_uuid.data = uuid
        form.name_ua.data = service.name_ua
        form.name_en.data = service.name_en
        form.parent_id.data = service.parent.id if service.parent else None

    return render_template("service/edit.html", form=form, service=service, parents=parents)


@service_route.route("/<uuid>/restore")
@login_required
def restore(uuid: str):
    service = db.session.scalar(m.Service.select().where(m.Service.uuid == uuid))
    link = request.referrer
    if not link:
        link = url_for("service.get_all", **arg_params())
    if not service:
        flash("Service not found", "error")
        values: Params = arg_params()
        log(log.ERROR, "Service not found: [%s]", uuid)
        return redirect(url_for("service.get_all", **values))
    service.is_deleted = False
    db.session.commit()
    flash("Service restored", "success")
    return redirect(link)


@service_route.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form: f.ServiceForm = f.ServiceForm()
    if form.validate_on_submit():
        parent = None
        if form.parent_id.data:
            parent = db.session.scalar(m.Service.select().where(m.Service.id == form.parent_id.data.id))
            if not parent:
                flash("Parent not found", "error")
                log(log.ERROR, "Parent not found: [%s]", form.parent_id.data)
                return redirect(url_for("service.get_all", **arg_params()))
        service = m.Service(
            name_ua=form.name_ua.data,
            name_en=form.name_en.data,
            parent_id=parent.id if parent else None,
        )
        service.save()
        log(log.INFO, "Form submitted. Service: [%s]", service)
        flash("Service created!!", "success")
        return redirect(url_for("service.get_all"))

    if form.errors:
        log(log.ERROR, "Form not submitted. Service:", form.errors)
        flash(f"Form validation error {form.errors}", "danger")

    return render_template("service/create.html", form=form)
