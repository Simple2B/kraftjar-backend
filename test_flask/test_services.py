import sqlalchemy as sa
from flask.testing import FlaskClient

from app import db
from app import models as m
from config import config

from .utils import login

CFG = config("testing")


# def test_export_services(runner: FlaskCliRunner):
#     res: Result = runner.invoke(args=["export-services"])
#     assert "done" in res.output
#     query = m.Service.select()
#     assert db.session.scalars(query).all()
#     assert len(db.session.scalars(query).all())


def test_list_all_services(populate: FlaskClient):
    client = populate
    login(client)
    res = client.get("/service/")
    assert res.status_code == 200
    db_services: list[m.Service] = db.session.scalars(
        m.Service.select()
        .where(m.Service.is_deleted == sa.false())
        .order_by(m.Service.id)
        .limit(CFG.DEFAULT_PAGE_SIZE + 1)
    ).all()
    # check first page data presents in the HTML
    for service in db_services[: CFG.DEFAULT_PAGE_SIZE]:
        assert service.name_en in res.text

    # check CFG.DEFAULT_PAGE_SIZE + 1 element is not present in the HTML
    assert db_services[-1].name_en not in res.text

    res = client.get(f"/service/?q={db_services[-1].name_en}")
    assert res.status_code == 200
    assert db_services[-1].name_en in res.text


def test_delete_service(populate: FlaskClient):
    client = populate
    login(client)
    service: m.Service | None = db.session.scalar(m.Service.select().order_by(m.Service.id))
    assert service
    name: str = service.name_en.replace(" ", "+")
    res = client.get(f"/service/{service.uuid}/delete?page=1&q={name}")
    assert res.status_code == 302
    assert f"/service/?page=1&q={name}" in res.location
    assert db.session.scalar(m.Service.select().where(m.Service.id == service.id)).is_deleted


def test_edit_service(populate: FlaskClient):
    client = populate
    login(client)
    service: m.Service | None = db.session.scalar(m.Service.select().order_by(m.Service.id))
    assert service
    res = client.get(f"/service/{service.uuid}/edit")
    assert res.status_code == 200
    assert service.name_en in res.text
    assert service.name_ua in res.text
    assert str(service.parent_id) in res.text
    assert "Save" in res.text


def test_save_service_form(populate: FlaskClient):
    client = populate
    login(client)
    service: m.Service | None = db.session.scalar(m.Service.select().order_by(m.Service.id))

    assert service
    name: str = service.name_en.replace(" ", "+")

    res = client.post(
        f"/service/{service.uuid}/edit?q={name}",
        data={
            "name_ua": "test_ua",
            "name_en": "test_en",
            "parent_id": 56,
        },
    )
    assert res.status_code == 302
    assert f"q={name}" in res.location

    service = db.session.scalar(m.Service.select().order_by(m.Service.id))
    assert service
    assert service.name_ua == "test_ua"
    assert service.name_en == "test_en"
    assert service.parent_id == 56
