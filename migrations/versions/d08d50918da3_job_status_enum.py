"""job_status_enum

Revision ID: d08d50918da3
Revises: 550a53dee628
Create Date: 2024-09-18 09:51:15.265967

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd08d50918da3'
down_revision = '550a53dee628'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    # Manual changes
    with op.batch_alter_table('jobs', schema=None) as batch_op:
        batch_op.execute("ALTER TYPE jobstatus ADD VALUE 'on_confirmation'")
        batch_op.execute("ALTER TYPE jobstatus ADD VALUE 'canceled'")
        batch_op.alter_column('status',
               existing_type=sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'ON_CONFIRMATION', 'CANCELED', 'ON_CONFIRMATION', 'CANCELED', name='jobstatus'),
               type_=sa.TEXT(),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
