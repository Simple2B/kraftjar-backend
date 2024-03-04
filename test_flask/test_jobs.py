from click.testing import Result
from flask.testing import FlaskClient, FlaskCliRunner

from app import db
from app import models as m
from config import config

CFG = config("testing")


def test_export_jobs(runner: FlaskCliRunner, populate: FlaskClient):
    res: Result = runner.invoke(args=["export-jobs"])
    assert "done" in res.output
    query = m.Job.select()
    assert db.session.scalars(query).all()


def test_export_jobs_in_json(runner: FlaskCliRunner, populate: FlaskClient):
    res: Result = runner.invoke(args=["export-jobs-in-json"])
    assert "done" in res.output
