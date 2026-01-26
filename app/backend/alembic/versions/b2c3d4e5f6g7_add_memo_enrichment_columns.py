"""Add memo enrichment columns (catalysts, conviction_breakdown, macro_context, position_sizing)

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add enrichment columns to memos table."""
    op.add_column('memos', sa.Column('catalysts', sa.JSON(), nullable=True))
    op.add_column('memos', sa.Column('conviction_breakdown', sa.JSON(), nullable=True))
    op.add_column('memos', sa.Column('macro_context', sa.JSON(), nullable=True))
    op.add_column('memos', sa.Column('position_sizing', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Remove enrichment columns from memos table."""
    op.drop_column('memos', 'position_sizing')
    op.drop_column('memos', 'macro_context')
    op.drop_column('memos', 'conviction_breakdown')
    op.drop_column('memos', 'catalysts')
