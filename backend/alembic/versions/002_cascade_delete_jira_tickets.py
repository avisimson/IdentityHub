"""Add ON DELETE CASCADE to tickets.jira_connection_id FK.

Without this, deleting a jira_connections row while tickets reference it
raises a foreign-key violation in PostgreSQL.

Revision ID: 002
Revises: 001
Create Date: 2026-04-08

"""
from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: str = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "tickets_jira_connection_id_fkey", "tickets", type_="foreignkey"
    )
    op.create_foreign_key(
        "tickets_jira_connection_id_fkey",
        "tickets",
        "jira_connections",
        ["jira_connection_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "tickets_jira_connection_id_fkey", "tickets", type_="foreignkey"
    )
    op.create_foreign_key(
        "tickets_jira_connection_id_fkey",
        "tickets",
        "jira_connections",
        ["jira_connection_id"],
        ["id"],
    )
