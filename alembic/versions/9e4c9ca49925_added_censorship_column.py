"""Added censorship column

Revision ID: 9e4c9ca49925
Revises: ea6425e582ab
Create Date: 2024-05-22 05:46:21.994859

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e4c9ca49925'
down_revision: Union[str, None] = 'ea6425e582ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('guilds', sa.Column('is_censored', sa.Boolean(), nullable=False, server_default=sa.sql.false()))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('guilds', 'is_censored')
    # ### end Alembic commands ###
