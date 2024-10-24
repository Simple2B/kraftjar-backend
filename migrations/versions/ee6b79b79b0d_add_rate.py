"""add Rate

Revision ID: ee6b79b79b0d
Revises: 18a7d53aa473
Create Date: 2024-10-17 17:45:13.149495

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ee6b79b79b0d'
down_revision = '18a7d53aa473'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('rates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('review', sa.String(length=1000), nullable=True))
        batch_op.drop_column('message')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('rates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('message', sa.VARCHAR(length=128), autoincrement=False, nullable=False))
        batch_op.drop_column('review')

    # ### end Alembic commands ###
