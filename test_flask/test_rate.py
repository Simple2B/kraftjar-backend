from click.testing import Result
from flask.testing import FlaskClient, FlaskCliRunner

from config import config

CFG = config("testing")


def test_rates(runner: FlaskCliRunner, populate: FlaskClient):
    res: Result = runner.invoke(args=["fix-rates"])
    assert "done" in res.output
