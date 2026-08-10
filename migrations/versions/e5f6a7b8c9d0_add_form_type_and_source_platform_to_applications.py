"""add form_type and source_platform to applications

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-09 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    # 幂等：检查列是否存在再添加
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = {c['name'] for c in inspector.get_columns('applications')}

    if 'form_type' not in existing_cols:
        op.add_column('applications',
            sa.Column('form_type', sa.String(length=50), nullable=True))
    if 'source_platform' not in existing_cols:
        op.add_column('applications',
            sa.Column('source_platform', sa.String(length=50), nullable=True))


def downgrade():
    op.drop_column('applications', 'source_platform')
    op.drop_column('applications', 'form_type')
