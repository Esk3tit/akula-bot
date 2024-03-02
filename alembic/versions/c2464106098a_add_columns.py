"""add columns

Revision ID: c2464106098a
Revises: 
Create Date: 2024-03-01 06:46:11.715510

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2464106098a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('streamers', sa.Column('streamer_name', sa.String()))
    op.add_column('streamers', sa.Column('topic_sub_id', sa.String()))


def downgrade() -> None:
    op.drop_column('streamers', 'streamer_name')
    op.drop_column('streamers', 'topic_sub_id')
