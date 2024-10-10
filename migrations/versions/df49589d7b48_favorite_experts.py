"""favorite_experts

Revision ID: df49589d7b48
Revises: 42e20253b857
Create Date: 2024-10-10 15:04:47.359939

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'df49589d7b48'
down_revision = '42e20253b857'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('favorite_experts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('expert_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['expert_id'], ['users.id'], name=op.f('fk_favorite_experts_expert_id_users')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_favorite_experts_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_favorite_experts'))
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('favorite_experts')
    # ### end Alembic commands ###