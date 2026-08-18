"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-17

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "empresas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nome_fantasia", sa.String(150), nullable=False),
        sa.Column("razao_social", sa.String(150)),
        sa.Column("cnpj", sa.String(20), unique=True),
        sa.Column("email", sa.String(150), nullable=False),
        sa.Column("telefone", sa.String(20)),
        sa.Column("endereco", sa.String(255)),
        sa.Column("cidade", sa.String(100)),
        sa.Column("estado", sa.String(2)),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    perfil_usuario = postgresql.ENUM("administrador", "gerente", "funcionario", name="perfil_usuario", create_type=False)
    perfil_usuario.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("email", sa.String(150), nullable=False, unique=True),
        sa.Column("senha_hash", sa.String(255), nullable=False),
        sa.Column("cargo", sa.String(100)),
        sa.Column("perfil", perfil_usuario, nullable=False, server_default="funcionario"),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ultimo_login", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_usuarios_empresa_id", "usuarios", ["empresa_id"])
    op.create_index("ix_usuarios_email", "usuarios", ["email"])

    op.create_table(
        "produtos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("codigo_barras", sa.String(50)),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("descricao", sa.String(500)),
        sa.Column("categoria", sa.String(100)),
        sa.Column("unidade_medida", sa.String(20), nullable=False, server_default="UN"),
        sa.Column("preco_custo", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("preco_venda", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("estoque_atual", sa.Integer, nullable=False, server_default="0"),
        sa.Column("estoque_minimo", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("empresa_id", "codigo_barras", name="uq_produto_empresa_codigo_barras"),
    )
    op.create_index("ix_produtos_empresa_id", "produtos", ["empresa_id"])
    op.create_index("ix_produtos_codigo_barras", "produtos", ["codigo_barras"])
    op.create_index("ix_produtos_categoria", "produtos", ["categoria"])

    status_lote = postgresql.ENUM("ativo", "proximo_vencimento", "vencido", "esgotado", "perdido", name="status_lote", create_type=False)
    status_lote.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "lotes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("produto_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("numero_lote", sa.String(50), nullable=False),
        sa.Column("quantidade", sa.Integer, nullable=False),
        sa.Column("data_validade", sa.Date, nullable=False),
        sa.Column("data_entrada", sa.Date, nullable=False),
        sa.Column("custo_unitario", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", status_lote, nullable=False, server_default="ativo"),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_lotes_empresa_id", "lotes", ["empresa_id"])
    op.create_index("ix_lotes_produto_id", "lotes", ["produto_id"])
    op.create_index("ix_lotes_data_validade", "lotes", ["data_validade"])
    op.create_index("ix_lotes_status", "lotes", ["status"])

    motivo_perda = postgresql.ENUM(
        "produto_vencido", "produto_danificado", "armazenamento_inadequado", "erro_de_estoque", "outro", name="motivo_perda", create_type=False
    )
    motivo_perda.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "perdas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("produto_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lote_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lotes.id", ondelete="SET NULL")),
        sa.Column("quantidade", sa.Integer, nullable=False),
        sa.Column("motivo", motivo_perda, nullable=False),
        sa.Column("valor_unitario", sa.Numeric(10, 2), nullable=False),
        sa.Column("valor_total", sa.Numeric(10, 2), nullable=False),
        sa.Column("data_perda", sa.Date, nullable=False),
        sa.Column("observacao", sa.String(500)),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_perdas_empresa_id", "perdas", ["empresa_id"])
    op.create_index("ix_perdas_produto_id", "perdas", ["produto_id"])
    op.create_index("ix_perdas_lote_id", "perdas", ["lote_id"])
    op.create_index("ix_perdas_data_perda", "perdas", ["data_perda"])

    tipo_alerta = postgresql.ENUM(
        "vencimento_7_dias", "vencimento_3_dias", "vencimento_1_dia", "vence_hoje", "vencido", "estoque_baixo", name="tipo_alerta", create_type=False
    )
    tipo_alerta.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "alertas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("produto_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lote_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lotes.id", ondelete="CASCADE")),
        sa.Column("tipo", tipo_alerta, nullable=False),
        sa.Column("mensagem", sa.String(500), nullable=False),
        sa.Column("data_alerta", sa.Date, nullable=False),
        sa.Column("lido", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("ignorado", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("lote_id", "tipo", name="uq_alerta_lote_tipo"),
    )
    op.create_index("ix_alertas_empresa_id", "alertas", ["empresa_id"])
    op.create_index("ix_alertas_produto_id", "alertas", ["produto_id"])
    op.create_index("ix_alertas_lote_id", "alertas", ["lote_id"])
    op.create_index("ix_alertas_tipo", "alertas", ["tipo"])
    op.create_index("ix_alertas_lido", "alertas", ["lido"])

    op.create_table(
        "configuracoes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("dias_alerta_1", sa.Integer, nullable=False, server_default="7"),
        sa.Column("dias_alerta_2", sa.Integer, nullable=False, server_default="3"),
        sa.Column("dias_alerta_3", sa.Integer, nullable=False, server_default="1"),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_configuracoes_empresa_id", "configuracoes", ["empresa_id"])

    plano_nome = postgresql.ENUM("gratuito", "basico", "profissional", name="plano_nome", create_type=False)
    plano_nome.create(op.get_bind(), checkfirst=True)
    status_assinatura = postgresql.ENUM(
        "trialing", "active", "past_due", "canceled", "unpaid", "incomplete", name="status_assinatura", create_type=False
    )
    status_assinatura.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("stripe_customer_id", sa.String(100)),
        sa.Column("stripe_subscription_id", sa.String(100)),
        sa.Column("stripe_price_id", sa.String(100)),
        sa.Column("plano", plano_nome, nullable=False, server_default="gratuito"),
        sa.Column("status", status_assinatura, nullable=False, server_default="active"),
        sa.Column("data_inicio", sa.Date),
        sa.Column("data_fim", sa.Date),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_subscriptions_empresa_id", "subscriptions", ["empresa_id"])


def downgrade() -> None:
    op.drop_table("subscriptions")
    op.drop_table("configuracoes")
    op.drop_table("alertas")
    op.drop_table("perdas")
    op.drop_table("lotes")
    op.drop_table("produtos")
    op.drop_table("usuarios")
    op.drop_table("empresas")

    bind = op.get_bind()
    for enum_name in ("status_assinatura", "plano_nome", "tipo_alerta", "motivo_perda", "status_lote", "perfil_usuario"):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
