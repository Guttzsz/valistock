"""mfa_secret_criptografado: amplia usuarios.mfa_secret para caber o segredo criptografado (Fernet)

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-26

"""
import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("usuarios", "mfa_secret", existing_type=sa.String(64), type_=sa.String(255), existing_nullable=True)


def downgrade() -> None:
    # Segredos ja criptografados nao cabem em 64 caracteres: quem tiver MFA ativo precisaria reconfigurar.
    op.alter_column("usuarios", "mfa_secret", existing_type=sa.String(255), type_=sa.String(64), existing_nullable=True)
