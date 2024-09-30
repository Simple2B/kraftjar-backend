"""user_description

Revision ID: 115cf9531d31
Revises: 67610acad186
Create Date: 2024-09-25 17:57:54.488254

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '115cf9531d31'
down_revision = '67610acad186'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('description', sa.String(length=512), server_default='', nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('description')

    # ### end Alembic commands ###