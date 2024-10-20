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
    def export_test_data_from_json():
        """Fill services, regions, rayons, cities, addresses with data from json file"""
        from .locations import export_test_locations_from_json_file
        from .cities import export_cities_from_json_file
        from .addresses import export_addresses_from_json_file
        from .locations import export_regions_from_json_file
        from .service import export_services_from_json_file
        from .rayons_json import export_rayons_from_json_file

        export_test_locations_from_json_file()
        export_services_from_json_file()
        export_regions_from_json_file()
        export_cities_from_json_file()
        export_rayons_from_json_file()
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

    @app.cli.command()
    def get_rayons():
        """Get rayons from Meest Express Public API"""
        from .rayons import get_rayons_from_meest_api

        get_rayons_from_meest_api()
        print("done")

    @app.cli.command()
    def get_settlements():
        """Get settlements from Meest Express Public API"""
        from .settlements import get_settlements_from_meest_api

        get_settlements_from_meest_api()
        print("done")

    @app.cli.command()
    @click.argument("lower_limit", type=int)
    @click.argument("upper_limit", type=int)
    def get_addresses(lower_limit: int, upper_limit: int):
        """Get addresses from Meest Express Public API"""
        from .addresses_api import get_addresses_from_meest_api

        get_addresses_from_meest_api(lower_limit, upper_limit)
        print("done")

    @app.cli.command()
    @click.argument("lower_limit", type=int)
    @click.argument("upper_limit", type=int)
    def update_addresses(lower_limit: int, upper_limit: int):
        """Update addresses from Meest Express Public API"""
        from .update_addresses_api import update_addresses_from_meest_api

        update_addresses_from_meest_api(lower_limit, upper_limit)
        print("done")

    @app.cli.command()
    @click.argument("region_id", type=int, required=False, default=10)
    @click.argument("district_id", type=str, required=False, default="a1e9f9b8-41b9-11df-907f-00215aee3ebe")
    @click.argument("city_id", type=str, required=False, default="91fc81db-266d-11e7-80fd-1c98ec135263")
    def filter_addresses(region_id: int, district_id: str, city_id: str):
        """Filter addresses"""
        from .filter import filter_addresses

        filter_addresses(region_id, district_id, city_id)
        print("done")
