from flask import render_template, Blueprint
from flask_login import login_required


main_blueprint = Blueprint("main", __name__)


@main_blueprint.route("/")
@login_required
def index():
    return render_template("index.html")


@main_blueprint.route("/policy")
def policy():
    return render_template("static/privacy_policy.html")
