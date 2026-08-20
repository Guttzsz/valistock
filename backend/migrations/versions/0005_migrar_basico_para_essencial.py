"""migra assinaturas com plano 'basico' (tier antigo, removido) para 'essencial'

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-20

"""
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE subscriptions SET plano = 'essencial' WHERE plano = 'basico'")


def downgrade() -> None:
    op.execute("UPDATE subscriptions SET plano = 'basico' WHERE plano = 'essencial'")
