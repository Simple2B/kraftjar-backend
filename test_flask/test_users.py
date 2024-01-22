from flask import current_app as app
from flask.testing import FlaskClient, FlaskCliRunner
from click.testing import Result
from app import models as m, db
from test_flask.utils import login
from api.utility import create_users


def test_list(populate: FlaskClient):
    login(populate)
    USERS_COUNT = 11
    create_users(db, USERS_COUNT)
    DEFAULT_PAGE_SIZE = app.config["DEFAULT_PAGE_SIZE"]
    response = populate.get("/user/")
    assert response
    assert response.status_code == 200
    html = response.data.decode()
    users = db.session.scalars(m.User.select().order_by(m.User.id).limit(USERS_COUNT)).all()
    assert len(users) == USERS_COUNT
    for user in users[:DEFAULT_PAGE_SIZE]:
        assert user.email in html
    assert users[10].email not in html

    populate.application.config["PAGE_LINKS_NUMBER"] = 6
    response = populate.get("/user/?page=6")
    assert response
    assert response.status_code == 200
    html = response.data.decode()
    assert "/user/?page=2" in html
    assert "/user/?page=1" in html
    assert "/user/?page=10" not in html
    assert "/user/?page=3" not in html


def test_create_user(runner: FlaskCliRunner):
    res: Result = runner.invoke(args=["create-users"])
    assert "users created" in res.output
    query = m.User.select()
    assert db.session.scalars(query).all()
    assert len(db.session.scalars(query).all())


def test_delete_user(populate: FlaskClient):
    login(populate)
    create_users(db)
    uc = db.session.query(m.User).count()
    response = populate.delete("/user/delete/1")
    assert response.status_code == 200
    assert db.session.query(m.User).count() < uc
