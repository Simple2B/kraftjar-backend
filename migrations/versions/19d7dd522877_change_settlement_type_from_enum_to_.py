"""change Settlement type from enum to string from SettlementType

Revision ID: 19d7dd522877
Revises: 550a53dee628
Create Date: 2024-09-19 10:16:03.764521

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '19d7dd522877'
down_revision = '550a53dee628'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('settlements', schema=None) as batch_op:
        batch_op.alter_column('type',
               existing_type=postgresql.ENUM('REGION_CENTER', 'RAYON_CENTER', 'CITY', 'VILLAGE', name='type'),
               type_=sa.String(),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('settlements', schema=None) as batch_op:
        batch_op.alter_column('type',
               existing_type=sa.String(),
               type_=postgresql.ENUM('REGION_CENTER', 'RAYON_CENTER', 'CITY', 'VILLAGE', name='type'),
               existing_nullable=False)

    # ### end Alembic commands ###
