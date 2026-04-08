"""Add encrypted_key column to api_keys table.

Stores the Fernet-encrypted raw API key so it can be copied from the UI
after creation.

Revision ID: 003
Revises: 002
Create Date: 2026-04-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: str = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "api_keys",
        sa.Column("encrypted_key", sa.LargeBinary(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("api_keys", "encrypted_key")
