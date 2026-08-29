"""mfa_totp: autenticacao em duas etapas via aplicativo autenticador (TOTP)

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-29

"""
import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("usuarios", sa.Column("mfa_secret", sa.String(64), nullable=True))
    op.add_column("usuarios", sa.Column("mfa_backup_codes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("usuarios", "mfa_backup_codes")
    op.drop_column("usuarios", "mfa_secret")
    op.drop_column("usuarios", "mfa_enabled")
