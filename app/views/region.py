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

region_route = Blueprint("region", __name__, url_prefix="/region")


@region_route.route("/", methods=["GET"])
@login_required
def get_all():
    q = request.args.get("q", type=str, default=None)
    query = m.Region.select().order_by(m.Region.id)
    count_query = sa.select(sa.func.count()).select_from(m.Region)
    if q:
        query = (
            m.Region.select()
            .where(m.Region.name_ua.ilike(f"{q}%") | m.Region.name_en.ilike(f"{q}%"))
            .order_by(m.Region.id)
        )
        count_query = (
            sa.select(sa.func.count())
            .where(m.Region.name_ua.ilike(f"{q}%") | m.Region.name_en.ilike(f"{q}%"))
            .select_from(m.Region)
        )

    pagination = create_pagination(total=db.session.scalar(count_query))
    regions = list(
        db.session.execute(
            query.offset((pagination.page - 1) * pagination.per_page).limit(pagination.per_page)
        ).scalars()
    )
    return render_template(
        "region/regions.html",
        regions=regions,
        page=pagination,
        search_query=q,
    )


@region_route.route("/<id>/delete")
@login_required
def delete(id: str):
    region = db.session.scalar(m.Region.select().where(m.Region.id == id))
    link = request.referrer
    if not link:
        link = url_for("region.get_all", **arg_params())
    if not region:
        flash("Region not found", "error")
        values: Params = arg_params()
        log(log.ERROR, "Service not found: [%s]", id)
        return redirect(url_for("region.get_all", **values))
    region.is_deleted = True
    db.session.commit()
    flash("Region deleted", "success")
    return redirect(link)


@region_route.route("/<id>/edit", methods=["GET", "POST"])
@login_required
def edit(id: str):
    region: m.Region = db.session.scalar(m.Region.select().where(m.Region.id == id))
    if not region:
        flash("Region not found", "error")
        log(log.ERROR, "Region not found: [%s]", id)
        return redirect(url_for("region.get_all", **arg_params()))

    form: f.RegionForm = f.RegionForm()

    if form.validate_on_submit():
        region.name_ua = form.name_ua.data.strip()
        region.name_en = form.name_en.data.strip()

        db.session.commit()
        flash("Region updated", "success")
        log(log.INFO, "Region updated: [%s]", region)
        return redirect(url_for("region.get_all", **arg_params()))

    elif form.is_submitted():
        flash(f"Form validation error {form.errors}", "danger")
        log(log.ERROR, "Form validation error: [%s]", form.errors)

    if not form.is_submitted():
        form.region_id.data = id
        form.name_ua.data = region.name_ua
        form.name_en.data = region.name_en

    return render_template("region/edit.html", form=form, region=region)


@region_route.route("/<id>/restore")
@login_required
def restore(id: str):
    region = db.session.scalar(m.Region.select().where(m.Region.id == id))
    link = request.referrer
    if not link:
        link = url_for("region.get_all", **arg_params())
    if not region:
        flash("Region not found", "error")
        values: Params = arg_params()
        log(log.ERROR, "Region not found: [%s]", id)
        return redirect(url_for("region.get_all", **values))
    region.is_deleted = False
    db.session.commit()
    flash("Region restored", "success")
    return redirect(link)
