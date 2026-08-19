"""stripe: super_admin, assinaturas expandidas, faturas, reembolsos, eventos_stripe

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-19

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("super_admin", sa.Boolean, nullable=False, server_default=sa.false()))

    op.add_column("subscriptions", sa.Column("valor_mensal", sa.Numeric(10, 2), nullable=False, server_default="0"))
    op.add_column("subscriptions", sa.Column("periodo_atual_fim", sa.Date))
    op.add_column("subscriptions", sa.Column("trial_fim", sa.Date))
    op.add_column("subscriptions", sa.Column("cancelar_ao_fim_periodo", sa.Boolean, nullable=False, server_default=sa.false()))

    status_fatura = postgresql.ENUM("paga", "pendente", "falhou", "reembolsada", name="status_fatura", create_type=False)
    status_fatura.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "faturas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscriptions.id", ondelete="SET NULL")),
        sa.Column("stripe_invoice_id", sa.String(100), nullable=False, unique=True),
        sa.Column("stripe_customer_id", sa.String(100)),
        sa.Column("numero", sa.String(50)),
        sa.Column("valor_total", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("valor_pago", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("moeda", sa.String(10), nullable=False, server_default="brl"),
        sa.Column("status", status_fatura, nullable=False),
        sa.Column("periodo_inicio", sa.Date),
        sa.Column("periodo_fim", sa.Date),
        sa.Column("url_fatura", sa.String(500)),
        sa.Column("url_pdf", sa.String(500)),
        sa.Column("pago_em", sa.DateTime(timezone=True)),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_faturas_empresa_id", "faturas", ["empresa_id"])
    op.create_index("ix_faturas_subscription_id", "faturas", ["subscription_id"])
    op.create_index("ix_faturas_stripe_invoice_id", "faturas", ["stripe_invoice_id"])
    op.create_index("ix_faturas_criado_em", "faturas", ["criado_em"])

    op.create_table(
        "reembolsos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fatura_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("faturas.id", ondelete="SET NULL")),
        sa.Column("stripe_refund_id", sa.String(100), nullable=False, unique=True),
        sa.Column("stripe_payment_intent_id", sa.String(100)),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column("motivo", sa.String(255)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_reembolsos_empresa_id", "reembolsos", ["empresa_id"])
    op.create_index("ix_reembolsos_fatura_id", "reembolsos", ["fatura_id"])

    op.create_table(
        "eventos_stripe",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stripe_event_id", sa.String(100), nullable=False, unique=True),
        sa.Column("tipo_evento", sa.String(100), nullable=False),
        sa.Column("processado", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("processado_em", sa.DateTime(timezone=True)),
        sa.Column("erro", sa.String(1000)),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_eventos_stripe_stripe_event_id", "eventos_stripe", ["stripe_event_id"])
    op.create_index("ix_eventos_stripe_tipo_evento", "eventos_stripe", ["tipo_evento"])


def downgrade() -> None:
    op.drop_table("eventos_stripe")
    op.drop_table("reembolsos")
    op.drop_table("faturas")

    bind = op.get_bind()
    postgresql.ENUM(name="status_fatura").drop(bind, checkfirst=True)

    op.drop_column("subscriptions", "cancelar_ao_fim_periodo")
    op.drop_column("subscriptions", "trial_fim")
    op.drop_column("subscriptions", "periodo_atual_fim")
    op.drop_column("subscriptions", "valor_mensal")

    op.drop_column("usuarios", "super_admin")
