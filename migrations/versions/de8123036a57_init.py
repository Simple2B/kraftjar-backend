"""init

Revision ID: de8123036a57
Revises: 
Create Date: 2024-01-18 12:56:07.643442

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'de8123036a57'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('files',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.String(length=36), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('type', sa.String(length=255), nullable=False),
    sa.Column('url', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_files'))
    )
    op.create_table('locations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_locations'))
    )
    op.create_table('professions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_professions'))
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.String(length=36), nullable=False),
    sa.Column('first_name', sa.String(length=64), nullable=False),
    sa.Column('last_name', sa.String(length=64), nullable=False),
    sa.Column('email', sa.String(length=128), nullable=False),
    sa.Column('phone', sa.String(length=32), nullable=False),
    sa.Column('google_id', sa.String(length=128), nullable=False),
    sa.Column('apple_id', sa.String(length=128), nullable=False),
    sa.Column('diia_id', sa.String(length=128), nullable=False),
    sa.Column('password_hash', sa.String(length=256), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('phone', name=op.f('uq_users_phone'))
    )
    op.create_table('addresses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.String(length=36), nullable=False),
    sa.Column('line1', sa.String(length=255), nullable=False),
    sa.Column('line2', sa.String(length=255), nullable=False),
    sa.Column('postcode', sa.String(length=255), nullable=False),
    sa.Column('city', sa.String(length=255), nullable=False),
    sa.Column('location_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['location_id'], ['locations.id'], name=op.f('fk_addresses_location_id_locations')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_addresses'))
    )
    op.create_table('services',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('profession_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['profession_id'], ['professions.id'], name=op.f('fk_services_profession_id_professions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_services'))
    )
    op.create_table('user_locations',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('location_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['location_id'], ['locations.id'], name=op.f('fk_user_locations_location_id_locations')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_locations_user_id_users')),
    sa.PrimaryKeyConstraint('user_id', 'location_id', name=op.f('pk_user_locations'))
    )
    op.create_table('user_professions',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('profession_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['profession_id'], ['professions.id'], name=op.f('fk_user_professions_profession_id_professions')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_professions_user_id_users')),
    sa.PrimaryKeyConstraint('user_id', 'profession_id', name=op.f('pk_user_professions'))
    )
    op.create_table('jobs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.String(length=36), nullable=False),
    sa.Column('title', sa.String(length=128), nullable=False),
    sa.Column('description', sa.String(length=512), nullable=False),
    sa.Column('address_id', sa.Integer(), nullable=False),
    sa.Column('time', sa.String(length=128), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', name='jobstatus'), nullable=False),
    sa.Column('is_public', sa.Boolean(), nullable=False),
    sa.Column('location_id', sa.Integer(), nullable=False),
    sa.Column('owner_id', sa.Integer(), nullable=False),
    sa.Column('worker_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['address_id'], ['addresses.id'], name=op.f('fk_jobs_address_id_addresses')),
    sa.ForeignKeyConstraint(['location_id'], ['locations.id'], name=op.f('fk_jobs_location_id_locations')),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name=op.f('fk_jobs_owner_id_users')),
    sa.ForeignKeyConstraint(['worker_id'], ['users.id'], name=op.f('fk_jobs_worker_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_jobs'))
    )
    op.create_table('applications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.String(length=36), nullable=False),
    sa.Column('worker_id', sa.Integer(), nullable=False),
    sa.Column('job_id', sa.Integer(), nullable=False),
    sa.Column('type', sa.Enum('INVITE', 'APPLY', name='applicationtype'), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'REJECTED', name='applicationstatus'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], name=op.f('fk_applications_job_id_jobs')),
    sa.ForeignKeyConstraint(['worker_id'], ['users.id'], name=op.f('fk_applications_worker_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_applications'))
    )
    op.create_table('job_files',
    sa.Column('file_id', sa.Integer(), nullable=False),
    sa.Column('job_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['file_id'], ['files.id'], name=op.f('fk_job_files_file_id_files')),
    sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], name=op.f('fk_job_files_job_id_jobs')),
    sa.PrimaryKeyConstraint('file_id', 'job_id', name=op.f('pk_job_files'))
    )
    op.create_table('job_services',
    sa.Column('service_id', sa.Integer(), nullable=False),
    sa.Column('job_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], name=op.f('fk_job_services_job_id_jobs')),
    sa.ForeignKeyConstraint(['service_id'], ['services.id'], name=op.f('fk_job_services_service_id_services')),
    sa.PrimaryKeyConstraint('service_id', 'job_id', name=op.f('pk_job_services'))
    )
    op.create_table('rates',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.String(length=36), nullable=False),
    sa.Column('message', sa.String(length=128), nullable=False),
    sa.Column('job_id', sa.Integer(), nullable=False),
    sa.Column('gives_id', sa.Integer(), nullable=False),
    sa.Column('receives_id', sa.Integer(), nullable=False),
    sa.Column('rate', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint('rate <= 5', name=op.f('ck_rates_max_rate_check')),
    sa.CheckConstraint('rate >= 1', name=op.f('ck_rates_min_rate_check')),
    sa.ForeignKeyConstraint(['gives_id'], ['users.id'], name=op.f('fk_rates_gives_id_users')),
    sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], name=op.f('fk_rates_job_id_jobs')),
    sa.ForeignKeyConstraint(['receives_id'], ['users.id'], name=op.f('fk_rates_receives_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_rates'))
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('rates')
    op.drop_table('job_services')
    op.drop_table('job_files')
    op.drop_table('applications')
    op.drop_table('jobs')
    op.drop_table('user_professions')
    op.drop_table('user_locations')
    op.drop_table('services')
    op.drop_table('addresses')
    op.drop_table('users')
    op.drop_table('professions')
    op.drop_table('locations')
    op.drop_table('files')
    # ### end Alembic commands ###