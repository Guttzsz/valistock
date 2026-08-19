"""categorias, fornecedores, localizacoes, campos personalizados, auditoria, movimentacoes de estoque, preferencias

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-18

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "categorias",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("descricao", sa.String(500)),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("empresa_id", "nome", name="uq_categoria_empresa_nome"),
    )
    op.create_index("ix_categorias_empresa_id", "categorias", ["empresa_id"])

    op.create_table(
        "fornecedores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("razao_social", sa.String(150)),
        sa.Column("cnpj", sa.String(20)),
        sa.Column("telefone", sa.String(20)),
        sa.Column("email", sa.String(150)),
        sa.Column("endereco", sa.String(255)),
        sa.Column("observacao", sa.String(500)),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_fornecedores_empresa_id", "fornecedores", ["empresa_id"])

    op.create_table(
        "localizacoes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("descricao", sa.String(255)),
        sa.Column("tipo", sa.String(50)),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_localizacoes_empresa_id", "localizacoes", ["empresa_id"])

    tipo_campo_personalizado = postgresql.ENUM(
        "texto", "numero", "data", "selecao", "booleano", name="tipo_campo_personalizado", create_type=False
    )
    tipo_campo_personalizado.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "campos_personalizados",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("tipo", tipo_campo_personalizado, nullable=False),
        sa.Column("obrigatorio", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("opcoes", sa.Text),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("empresa_id", "nome", name="uq_campo_personalizado_empresa_nome"),
    )
    op.create_index("ix_campos_personalizados_empresa_id", "campos_personalizados", ["empresa_id"])

    op.create_table(
        "valores_campos_personalizados",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("campo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campos_personalizados.id", ondelete="CASCADE"), nullable=False),
        sa.Column("produto_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("valor", sa.Text),
        sa.UniqueConstraint("campo_id", "produto_id", name="uq_valor_campo_produto"),
    )
    op.create_index("ix_valores_campos_personalizados_campo_id", "valores_campos_personalizados", ["campo_id"])
    op.create_index("ix_valores_campos_personalizados_produto_id", "valores_campos_personalizados", ["produto_id"])

    op.create_table(
        "logs_auditoria",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL")),
        sa.Column("usuario_nome", sa.String(150)),
        sa.Column("acao", sa.String(100), nullable=False),
        sa.Column("entidade", sa.String(50), nullable=False),
        sa.Column("entidade_id", postgresql.UUID(as_uuid=True)),
        sa.Column("descricao", sa.Text, nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_logs_auditoria_empresa_id", "logs_auditoria", ["empresa_id"])
    op.create_index("ix_logs_auditoria_usuario_id", "logs_auditoria", ["usuario_id"])
    op.create_index("ix_logs_auditoria_acao", "logs_auditoria", ["acao"])
    op.create_index("ix_logs_auditoria_entidade", "logs_auditoria", ["entidade"])
    op.create_index("ix_logs_auditoria_criado_em", "logs_auditoria", ["criado_em"])

    tipo_movimentacao = postgresql.ENUM(
        "entrada", "saida", "ajuste", "perda", "venda", name="tipo_movimentacao", create_type=False
    )
    tipo_movimentacao.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "movimentacoes_estoque",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("produto_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lote_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lotes.id", ondelete="SET NULL")),
        sa.Column("tipo", tipo_movimentacao, nullable=False),
        sa.Column("quantidade", sa.Integer, nullable=False),
        sa.Column("estoque_resultante", sa.Integer, nullable=False),
        sa.Column("motivo", sa.String(255)),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_movimentacoes_estoque_empresa_id", "movimentacoes_estoque", ["empresa_id"])
    op.create_index("ix_movimentacoes_estoque_produto_id", "movimentacoes_estoque", ["produto_id"])
    op.create_index("ix_movimentacoes_estoque_lote_id", "movimentacoes_estoque", ["lote_id"])
    op.create_index("ix_movimentacoes_estoque_tipo", "movimentacoes_estoque", ["tipo"])
    op.create_index("ix_movimentacoes_estoque_criado_em", "movimentacoes_estoque", ["criado_em"])

    op.create_table(
        "preferencias_notificacao",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("produtos_vencendo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("produtos_vencidos", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("estoque_baixo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("novas_perdas", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("relatorios", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("avisos_administrativos", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_preferencias_notificacao_usuario_id", "preferencias_notificacao", ["usuario_id"])

    op.create_table(
        "preferencias_dashboard",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("widgets_ativos", sa.Text, nullable=False, server_default=""),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_preferencias_dashboard_usuario_id", "preferencias_dashboard", ["usuario_id"])

    # Configuracoes: identidade da empresa + onboarding
    op.add_column("configuracoes", sa.Column("tipo_estabelecimento", sa.String(50)))
    op.add_column("configuracoes", sa.Column("fuso_horario", sa.String(50), nullable=False, server_default="America/Sao_Paulo"))
    op.add_column("configuracoes", sa.Column("moeda", sa.String(10), nullable=False, server_default="BRL"))
    op.add_column("configuracoes", sa.Column("formato_data", sa.String(20), nullable=False, server_default="DD/MM/AAAA"))
    op.add_column("configuracoes", sa.Column("cor_principal", sa.String(20), nullable=False, server_default="#16a34a"))
    op.add_column("configuracoes", sa.Column("logo_url", sa.String(500)))
    op.add_column("configuracoes", sa.Column("horario_funcionamento", sa.String(255)))
    op.add_column("configuracoes", sa.Column("onboarding_concluido", sa.Boolean, nullable=False, server_default=sa.false()))
    op.add_column("configuracoes", sa.Column("onboarding_etapa", sa.Integer, nullable=False, server_default="1"))
    op.add_column("configuracoes", sa.Column("quantidade_funcionarios_aprox", sa.String(20)))
    op.add_column("configuracoes", sa.Column("quantidade_produtos_aprox", sa.String(20)))

    # Produtos: marca, categoria (agora entidade), fornecedor, localizacao
    op.add_column("produtos", sa.Column("marca", sa.String(100)))
    op.add_column("produtos", sa.Column("categoria_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categorias.id", ondelete="SET NULL")))
    op.add_column("produtos", sa.Column("fornecedor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fornecedores.id", ondelete="SET NULL")))
    op.add_column("produtos", sa.Column("localizacao_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("localizacoes.id", ondelete="SET NULL")))
    op.create_index("ix_produtos_categoria_id", "produtos", ["categoria_id"])
    op.create_index("ix_produtos_fornecedor_id", "produtos", ["fornecedor_id"])
    op.create_index("ix_produtos_localizacao_id", "produtos", ["localizacao_id"])

    # Migra os valores de texto livre produtos.categoria para categorias reais da empresa
    op.execute(
        """
        INSERT INTO categorias (id, empresa_id, nome, ativo, criado_em, atualizado_em)
        SELECT gen_random_uuid(), d.empresa_id, d.categoria, true, now(), now()
        FROM (SELECT DISTINCT empresa_id, categoria FROM produtos WHERE categoria IS NOT NULL AND categoria <> '') AS d
        """
    )
    op.execute(
        """
        UPDATE produtos p
        SET categoria_id = c.id
        FROM categorias c
        WHERE c.empresa_id = p.empresa_id AND c.nome = p.categoria
        """
    )

    op.drop_index("ix_produtos_categoria", table_name="produtos")
    op.drop_column("produtos", "categoria")

    # Lotes: localizacao especifica pode sobrescrever a do produto
    op.add_column("lotes", sa.Column("localizacao_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("localizacoes.id", ondelete="SET NULL")))
    op.create_index("ix_lotes_localizacao_id", "lotes", ["localizacao_id"])


def downgrade() -> None:
    op.drop_index("ix_lotes_localizacao_id", table_name="lotes")
    op.drop_column("lotes", "localizacao_id")

    op.add_column("produtos", sa.Column("categoria", sa.String(100)))
    op.execute(
        """
        UPDATE produtos p
        SET categoria = c.nome
        FROM categorias c
        WHERE c.id = p.categoria_id
        """
    )
    op.create_index("ix_produtos_categoria", "produtos", ["categoria"])

    op.drop_index("ix_produtos_localizacao_id", table_name="produtos")
    op.drop_index("ix_produtos_fornecedor_id", table_name="produtos")
    op.drop_index("ix_produtos_categoria_id", table_name="produtos")
    op.drop_column("produtos", "localizacao_id")
    op.drop_column("produtos", "fornecedor_id")
    op.drop_column("produtos", "categoria_id")

    op.drop_column("configuracoes", "quantidade_produtos_aprox")
    op.drop_column("configuracoes", "quantidade_funcionarios_aprox")
    op.drop_column("configuracoes", "onboarding_etapa")
    op.drop_column("configuracoes", "onboarding_concluido")
    op.drop_column("configuracoes", "horario_funcionamento")
    op.drop_column("configuracoes", "logo_url")
    op.drop_column("configuracoes", "cor_principal")
    op.drop_column("configuracoes", "formato_data")
    op.drop_column("configuracoes", "moeda")
    op.drop_column("configuracoes", "fuso_horario")
    op.drop_column("configuracoes", "tipo_estabelecimento")

    op.drop_table("preferencias_dashboard")
    op.drop_table("preferencias_notificacao")
    op.drop_table("movimentacoes_estoque")
    op.drop_table("logs_auditoria")
    op.drop_table("valores_campos_personalizados")
    op.drop_table("campos_personalizados")
    op.drop_table("localizacoes")
    op.drop_table("fornecedores")
    op.drop_table("categorias")

    bind = op.get_bind()
    for enum_name in ("tipo_movimentacao", "tipo_campo_personalizado"):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
