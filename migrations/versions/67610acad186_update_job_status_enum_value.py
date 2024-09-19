"""update_job_status_enum_value

Revision ID: 67610acad186
Revises: 19d7dd522877
Create Date: 2024-09-19 12:03:45.045803

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '67610acad186'
down_revision = '19d7dd522877'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('jobs', schema=None) as batch_op:
        batch_op.alter_column('status',
               existing_type=sa.TEXT(),
               type_=sa.String(length=36),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('jobs', schema=None) as batch_op:
        batch_op.alter_column('status',
               existing_type=sa.String(length=36),
               type_=sa.TEXT(),
               existing_nullable=False)

    # ### end Alembic commands ###