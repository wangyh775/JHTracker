"""add submission tables (answer_bank, experience_bank, application_submissions)

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    # 可复用求职答案库（敏感答案不入库，从 profile.md 直通）
    op.create_table('answer_bank',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_pattern', sa.String(length=200), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('role_family', sa.String(length=100), nullable=True),
        sa.Column('needs_review', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('source', sa.String(length=20), nullable=True, server_default='manual'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_answer_bank_question_pattern', 'answer_bank', ['question_pattern'], unique=False)
    op.create_index('ix_answer_bank_role_family', 'answer_bank', ['role_family'], unique=False)

    # 按岗位族路由的经历片段库
    op.create_table('experience_bank',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_family', sa.String(length=100), nullable=False),
        sa.Column('bullet_text', sa.Text(), nullable=False),
        sa.Column('jd_keywords', sa.String(length=500), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_experience_bank_role_family', 'experience_bank', ['role_family'], unique=False)

    # 网申预填执行记录
    op.create_table('application_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('form_url', sa.String(length=500), nullable=False),
        sa.Column('prefilled_data', sa.Text(), nullable=True),
        sa.Column('agent_trace_id', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='prefilled'),
        sa.Column('human_approved_at', sa.DateTime(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('screenshot_path', sa.String(length=500), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_application_submissions_application_id', 'application_submissions', ['application_id'], unique=False)


def downgrade():
    op.drop_index('ix_application_submissions_application_id', table_name='application_submissions')
    op.drop_table('application_submissions')

    op.drop_index('ix_experience_bank_role_family', table_name='experience_bank')
    op.drop_table('experience_bank')

    op.drop_index('ix_answer_bank_role_family', table_name='answer_bank')
    op.drop_index('ix_answer_bank_question_pattern', table_name='answer_bank')
    op.drop_table('answer_bank')
