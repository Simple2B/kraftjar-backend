import click
import sqlalchemy as sa
from flask import Flask
from sqlalchemy import orm

from app import db, forms
from app import models as m
from app import schema as s


def init(app: Flask):
    # flask cli context setup
    @app.shell_context_processor
    def get_context():
        """Objects exposed here will be automatically available from the shell."""
        return dict(app=app, db=db, m=m, f=forms, s=s, sa=sa, orm=orm)

    if app.config["ENV"] != "production":

        @app.cli.command()
        @click.option("--count", default=100, type=int)
        def db_populate(count: int):
            """Fill DB by dummy data."""
            from test_flask.db import populate

            populate(count)
            print(f"DB populated by {count} instancies")

    @app.cli.command("create-admin")
    def create_admin():
        """Create super admin account"""
        query = m.Admin.select().where(m.Admin.email == app.config["ADMIN_EMAIL"])
        if db.session.execute(query).first():
            print(f"User with e-mail: [{app.config['ADMIN_EMAIL']}] already exists")
            return
        m.Admin(
            username=app.config["ADMIN_USERNAME"],
            email=app.config["ADMIN_EMAIL"],
            password=app.config["ADMIN_PASSWORD"],
        ).save()
        print("admin created")

    if app.config["ENV"] != "production":

        @app.cli.command("create-users")
        def create_users():
            """Create users"""
            from test_flask.utility import create_users

            create_users(db)
            print("users created")

    @app.cli.command("export-users")
    def export_users():
        """Creates records in user table from json"""
        from .user import export_users_from_json_file

        export_users_from_json_file()
        print("done")

    @app.cli.command()
    def export_services():
        """Fill services with data from json file"""
        from .service import export_services_from_json_file

        export_services_from_json_file()
        print("done")

    @app.cli.command()
    def export_regions():
        """Fill regions with data from json file"""
        from .locations import export_regions_from_json_file

        export_regions_from_json_file()
        print("done")

    @app.cli.command()
    def export_addresses():
        """Fill addresses with data from json file"""
        from .addresses import export_addresses_from_json_file

        export_addresses_from_json_file()
        print("done")

    @app.cli.command()
    def export_services_regions_addresses():
        """Fill services, regions, addresses with data from json file"""
        from .addresses import export_addresses_from_json_file
        from .locations import export_regions_from_json_file
        from .service import export_services_from_json_file

        export_services_from_json_file()
        export_regions_from_json_file()
        export_addresses_from_json_file()

        print("done")

    @app.cli.command()
    def write_phones():
        """Write phones to google spreadsheets"""
        from .user import write_phone_to_google_spreadsheets

        write_phone_to_google_spreadsheets()
        print("done")

    @app.cli.command()
    def write_emails():
        """Write emails to google spreadsheets"""
        from .user import write_email_to_google_spreadsheets

        write_email_to_google_spreadsheets()
        print("done")

    @app.cli.command()
    def fill_db_with_users():
        """Fill users with data from google spreadsheets"""
        from .user import export_users_from_google_spreadsheets

        export_users_from_google_spreadsheets()
        print("done")

    @app.cli.command()
    def fill_db_with_jobs():
        """Fill jobs with data from google spreadsheets"""
        from .job import export_jobs_from_google_spreadsheets

        export_jobs_from_google_spreadsheets()
        print("done")

    @app.cli.command()
    def fill_stage_db():
        """Fill users and contacts (job) with data from google spreadsheets"""
        from .job import export_jobs_from_google_spreadsheets
        from .user import export_users_from_google_spreadsheets

        export_users_from_google_spreadsheets()
        export_jobs_from_google_spreadsheets()
        print("done")

    if app.config["ENV"] != "production":

        @app.cli.command()
        def export_jobs_in_json():
            """Export jobs to json file"""
            from .job import export_jobs_from_google_spreadsheets

            export_jobs_from_google_spreadsheets(in_json=True)
            print("done")

    if app.config["ENV"] != "production":

        @app.cli.command()
        def export_users_in_json():
            """Export users to json file"""
            from .user import export_users_from_google_spreadsheets

            export_users_from_google_spreadsheets(in_json=True)
            print("done")

    @app.cli.command()
    def export_jobs():
        """Fill jobs with data from json file"""
        from .job import export_jobs_from_json_file

        export_jobs_from_json_file()
        print("done")

    @app.cli.command()
    def fix_rates():
        """Fix rates"""
        from .rate import fix_users_average_rate

        fix_users_average_rate()
        print("done")
