"""redefinicoes_senha: tokens de uso unico para recuperar a senha por e-mail

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-19

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "redefinicoes_senha",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_redefinicoes_senha_usuario_id", "redefinicoes_senha", ["usuario_id"])
    op.create_index("ix_redefinicoes_senha_token_hash", "redefinicoes_senha", ["token_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_redefinicoes_senha_token_hash", table_name="redefinicoes_senha")
    op.drop_index("ix_redefinicoes_senha_usuario_id", table_name="redefinicoes_senha")
    op.drop_table("redefinicoes_senha")
