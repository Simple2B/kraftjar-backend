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
