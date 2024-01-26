from flask.testing import FlaskCliRunner
from click.testing import Result
from app import models as m, db


def test_export_regions(runner: FlaskCliRunner):
    res: Result = runner.invoke(args=["export-regions"])
    assert "done" in res.output
    query = m.Region.select()
    assert db.session.scalars(query).all()
    assert len(db.session.scalars(query).all())
