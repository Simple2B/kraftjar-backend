from flask import current_app as app
from flask.testing import FlaskClient, FlaskCliRunner
from click.testing import Result
from app import models as m, db
from test_flask.utils import login


def test_list(populate: FlaskClient):
    login(populate)
    DEFAULT_PAGE_SIZE = app.config["DEFAULT_PAGE_SIZE"]
    response = populate.get("/admin/")
    assert response
    assert response.status_code == 200
    html = response.data.decode()
    users = db.session.scalars(m.Admin.select().order_by(m.Admin.id).limit(11)).all()
    assert len(users) == 11
    for user in users[:DEFAULT_PAGE_SIZE]:
        assert user.username in html
    assert users[10].username not in html

    populate.application.config["PAGE_LINKS_NUMBER"] = 6
    response = populate.get("/admin/?page=6")
    assert response
    assert response.status_code == 200
    html = response.data.decode()
    assert "/admin/?page=6" in html
    assert "/admin/?page=3" in html
    assert "/admin/?page=8" in html
    assert "/admin/?page=10" not in html
    assert "/admin/?page=2" not in html


def test_create_admin(runner: FlaskCliRunner):
    res: Result = runner.invoke(args=["create-admin"])
    assert "admin created" in res.output
    query = m.Admin.select().where(m.Admin.username == app.config["ADMIN_USERNAME"])
    assert db.session.scalar(query)


def test_populate_db(runner: FlaskCliRunner):
    TEST_COUNT = 56
    count_before = db.session.query(m.Admin).count()
    res: Result = runner.invoke(args=["db-populate", "--count", f"{TEST_COUNT}"])
    assert f"populated by {TEST_COUNT}" in res.stdout
    assert (db.session.query(m.Admin).count() - count_before) == TEST_COUNT


def test_delete_user(populate: FlaskClient):
    login(populate)
    response = populate.delete("/admin/delete/1")
    assert response.status_code == 200
    assert db.session.scalar(m.Admin.select().where(m.Admin.id == 1)).is_deleted
