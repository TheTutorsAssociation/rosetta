"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-07 00:00:00.000000

This is the seed migration. It is hand-written to match the models in ``app/`` so the schema
exists before the dependencies are installed; the canonical way to (re)generate migrations from
the models is ``uv run alembic revision --autogenerate`` (or ``uv run python migrations/client.py
create``). CI runs ``alembic upgrade head`` against a clean database to prove this migration
applies and stays in sync with the models.
"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

import app.common.fields

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'user',
        sa.Column('first_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('last_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('role', sa.Enum('admin', 'member', name='userrole'), nullable=True),
        sa.Column('is_superadmin', sa.Boolean(), nullable=False),
        sa.Column('created_dt', app.common.fields.UTCDateTime(timezone=True), nullable=True),
        sa.Column('updated_dt', app.common.fields.UTCDateTime(timezone=True), nullable=True),
        sa.Column('deleted_dt', app.common.fields.UTCDateTime(timezone=True), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_user_created_dt'), 'user', ['created_dt'], unique=False)
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_index(op.f('ix_user_created_dt'), table_name='user')
    op.drop_table('user')

    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
