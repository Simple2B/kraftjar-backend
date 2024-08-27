import sqlalchemy as sa
from click.testing import Result
from flask.testing import FlaskClient, FlaskCliRunner

from app import db
from app import models as m
from config import config

from .utils import login

CFG = config("testing")


def test_export_regions(runner: FlaskCliRunner):
    res: Result = runner.invoke(args=["export-regions"])
    assert "done" in res.output
    query = m.Region.select()
    assert db.session.scalars(query).all()
    assert len(db.session.scalars(query).all())


def test_list_all_regions(populate: FlaskClient):
    client = populate
    login(client)
    res = client.get("/region/")
    assert res.status_code == 200
    db_regions: list[m.Region] = db.session.scalars(
        m.Region.select().where(m.Region.is_deleted.is_(False)).order_by(m.Region.id).limit(CFG.DEFAULT_PAGE_SIZE + 1)
    ).all()
    # check first page data presents in the HTML
    for region in db_regions[: CFG.DEFAULT_PAGE_SIZE]:
        assert region.name_ua in res.text
    # check CFG.DEFAULT_PAGE_SIZE + 1 element is not present in the HTML
    assert db_regions[-1].name_ua not in res.text

    res = client.get(f"/service/?q={db_regions[-1].name_en}")
    assert res.status_code == 200
    assert db_regions[-1].name_en in res.text
