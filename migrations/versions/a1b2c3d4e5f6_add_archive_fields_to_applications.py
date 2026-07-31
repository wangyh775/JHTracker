"""add archive fields to applications

Revision ID: a1b2c3d4e5f6
Revises: 3ccaa5ea3b4a
Create Date: 2026-07-31 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = '3ccaa5ea3b4a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_archived', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('archived_at', sa.DateTime(), nullable=True))
        batch_op.create_index('ix_applications_is_archived', ['is_archived'], unique=False)


def downgrade():
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.drop_index('ix_applications_is_archived')
        batch_op.drop_column('archived_at')
        batch_op.drop_column('is_archived')
