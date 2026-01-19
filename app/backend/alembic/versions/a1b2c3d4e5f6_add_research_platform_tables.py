"""Add research platform tables (memos, investments, analyst_stats)

Revision ID: a1b2c3d4e5f6
Revises: d5e78f9a1b2c
Create Date: 2026-01-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'd5e78f9a1b2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create memos table
    op.create_table('memos',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('ticker', sa.String(length=10), nullable=False),
        sa.Column('analyst', sa.String(length=50), nullable=False),
        sa.Column('signal', sa.String(length=10), nullable=False),
        sa.Column('conviction', sa.Integer(), nullable=False),
        sa.Column('thesis', sa.Text(), nullable=False),
        sa.Column('bull_case', sa.JSON(), nullable=False),
        sa.Column('bear_case', sa.JSON(), nullable=False),
        sa.Column('metrics', sa.JSON(), nullable=False),
        sa.Column('current_price', sa.Float(), nullable=False),
        sa.Column('target_price', sa.Float(), nullable=False),
        sa.Column('time_horizon', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_memos_analyst'), 'memos', ['analyst'], unique=False)
    op.create_index(op.f('ix_memos_status'), 'memos', ['status'], unique=False)
    op.create_index(op.f('ix_memos_ticker'), 'memos', ['ticker'], unique=False)

    # Create investments table
    op.create_table('investments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('memo_id', sa.String(length=36), nullable=False),
        sa.Column('ticker', sa.String(length=10), nullable=False),
        sa.Column('analyst', sa.String(length=50), nullable=False),
        sa.Column('signal', sa.String(length=10), nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=False),
        sa.Column('entry_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('exit_price', sa.Float(), nullable=True),
        sa.Column('exit_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['memo_id'], ['memos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_investments_analyst'), 'investments', ['analyst'], unique=False)
    op.create_index(op.f('ix_investments_memo_id'), 'investments', ['memo_id'], unique=False)
    op.create_index(op.f('ix_investments_status'), 'investments', ['status'], unique=False)
    op.create_index(op.f('ix_investments_ticker'), 'investments', ['ticker'], unique=False)

    # Create analyst_stats table
    op.create_table('analyst_stats',
        sa.Column('analyst', sa.String(length=50), nullable=False),
        sa.Column('total_memos', sa.Integer(), nullable=True),
        sa.Column('approved_count', sa.Integer(), nullable=True),
        sa.Column('win_count', sa.Integer(), nullable=True),
        sa.Column('total_return', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('analyst')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('analyst_stats')
    op.drop_index(op.f('ix_investments_ticker'), table_name='investments')
    op.drop_index(op.f('ix_investments_status'), table_name='investments')
    op.drop_index(op.f('ix_investments_memo_id'), table_name='investments')
    op.drop_index(op.f('ix_investments_analyst'), table_name='investments')
    op.drop_table('investments')
    op.drop_index(op.f('ix_memos_ticker'), table_name='memos')
    op.drop_index(op.f('ix_memos_status'), table_name='memos')
    op.drop_index(op.f('ix_memos_analyst'), table_name='memos')
    op.drop_table('memos')
