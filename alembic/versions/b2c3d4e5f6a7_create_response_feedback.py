"""create_response_feedback

Revision ID: b2c3d4e5f6a7
Revises: f2aa7b9accff
Create Date: 2026-04-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'f2aa7b9accff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'response_feedback',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('source_qa_pair_id', sa.String(length=36), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=False),
        sa.Column('span_start', sa.Integer(), nullable=True),
        sa.Column('span_end', sa.Integer(), nullable=True),
        sa.Column('problem', sa.Text(), nullable=False),
        sa.Column('desired_behavior', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            '(span_start IS NULL AND span_end IS NULL) OR '
            '(span_start >= 0 AND span_end > span_start)',
            name='ck_response_feedback_span_valid',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('response_feedback', schema=None) as batch_op:
        batch_op.create_index(
            'idx_response_feedback_source_qa_pair_id', ['source_qa_pair_id'], unique=False,
        )
        batch_op.create_index(
            'idx_response_feedback_created_at', ['created_at'], unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table('response_feedback', schema=None) as batch_op:
        batch_op.drop_index('idx_response_feedback_created_at')
        batch_op.drop_index('idx_response_feedback_source_qa_pair_id')
    op.drop_table('response_feedback')
