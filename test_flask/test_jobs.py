from click.testing import Result
from flask.testing import FlaskClient, FlaskCliRunner
import pytest

from app import db
from app import models as m
from config import config

CFG = config("testing")


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_export_jobs(runner: FlaskCliRunner, populate: FlaskClient):
    res: Result = runner.invoke(args=["export-jobs"])
    assert "done" in res.output
    query = m.Job.select()
    assert db.session.scalars(query).all()
