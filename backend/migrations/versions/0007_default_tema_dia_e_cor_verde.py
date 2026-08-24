"""restaura tema/cor padrao do site (dia/verde) e migra usuarios ainda no default antigo

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-24

"""
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE usuarios ALTER COLUMN theme SET DEFAULT 'dia'")
    op.execute("ALTER TABLE usuarios ALTER COLUMN accent_color SET DEFAULT 'verde'")
    op.execute("UPDATE usuarios SET theme = 'dia' WHERE theme = 'automatico'")
    op.execute("UPDATE usuarios SET accent_color = 'verde' WHERE accent_color = 'azul'")


def downgrade() -> None:
    op.execute("ALTER TABLE usuarios ALTER COLUMN theme SET DEFAULT 'automatico'")
    op.execute("ALTER TABLE usuarios ALTER COLUMN accent_color SET DEFAULT 'azul'")
