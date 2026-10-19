"""termos_aceitos_em: registra quando o usuario aceitou os Termos de Uso e a Politica de Privacidade

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-19

"""
import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("termos_aceitos_em", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("usuarios", "termos_aceitos_em")
