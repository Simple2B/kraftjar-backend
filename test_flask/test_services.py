from flask.testing import FlaskCliRunner
from click.testing import Result
from app import models as m, db


def test_export_services(runner: FlaskCliRunner):
    res: Result = runner.invoke(args=["export-services"])
    assert "done" in res.output
    query = m.Field.select()
    assert db.session.scalars(query).all()
    assert len(db.session.scalars(query).all())
