"""planos 5 tiers (essencial/empresa/rede) + aparencia (theme/accent_color) do usuario

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-20

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Novo valor de enum Postgres nao pode ser usado na mesma transacao em que foi
    # criado, entao a migracao de dados (basico -> essencial) fica na 0005.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE plano_nome ADD VALUE IF NOT EXISTS 'essencial'")
        op.execute("ALTER TYPE plano_nome ADD VALUE IF NOT EXISTS 'empresa'")
        op.execute("ALTER TYPE plano_nome ADD VALUE IF NOT EXISTS 'rede'")

    tema_usuario = postgresql.ENUM("dia", "noite", "automatico", name="tema_usuario", create_type=False)
    tema_usuario.create(op.get_bind(), checkfirst=True)
    cor_destaque = postgresql.ENUM(
        "azul", "verde", "roxo", "laranja", "vermelho", "ciano", "rosa", "amarelo", name="cor_destaque", create_type=False
    )
    cor_destaque.create(op.get_bind(), checkfirst=True)

    op.add_column("usuarios", sa.Column("theme", tema_usuario, nullable=False, server_default="automatico"))
    op.add_column("usuarios", sa.Column("accent_color", cor_destaque, nullable=False, server_default="azul"))


def downgrade() -> None:
    op.drop_column("usuarios", "accent_color")
    op.drop_column("usuarios", "theme")

    bind = op.get_bind()
    postgresql.ENUM(name="cor_destaque").drop(bind, checkfirst=True)
    postgresql.ENUM(name="tema_usuario").drop(bind, checkfirst=True)

    # Nao ha downgrade para remover valores de plano_nome (Postgres nao suporta
    # DROP VALUE em enum) — os valores essencial/empresa/rede ficam no tipo,
    # simplesmente sem linhas usando-os apos o downgrade dos dados (ver 0005).
