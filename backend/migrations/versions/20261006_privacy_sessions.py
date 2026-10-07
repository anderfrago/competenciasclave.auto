"""Revocable sessions and account deactivation."""
from alembic import op
import sqlalchemy as sa

revision = "20261006_privacy_sessions"
down_revision = "7182b36853ab"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("auth_attempts",
                    sa.Column("key", sa.String(64), primary_key=True),
                    sa.Column("hits", sa.Integer(), nullable=False),
                    sa.Column("expires_at", sa.Integer(), nullable=False))
    op.create_index("ix_auth_attempts_expires_at", "auth_attempts", ["expires_at"])
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch.add_column(sa.Column("auth_version", sa.Integer(), nullable=False, server_default="1"))


def downgrade():
    op.drop_table("auth_attempts")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("auth_version")
        batch.drop_column("active")
