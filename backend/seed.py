"""Popula o banco com dados de demonstracao: Mercado Sao Joao.

Uso: python seed.py
"""
import uuid
from datetime import timedelta
from decimal import Decimal

from app.auth.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models.categoria import Categoria
from app.models.configuracao import Configuracao
from app.models.empresa import Empresa
from app.models.fornecedor import Fornecedor
from app.models.localizacao import Localizacao
from app.models.lote import Lote, StatusLote
from app.models.perda import MotivoPerda, Perda
from app.models.produto import Produto
from app.models.usuario import PerfilUsuario, Usuario
from app.services.financeiro_service import valor_total_perda
from app.utils.timezone import today

PRODUTOS_DEMO = [
    # nome, categoria, unidade, custo, venda, estoque_minimo, localizacao
    ("Leite Integral 1L", "Laticinios", "UN", Decimal("4.20"), Decimal("6.50"), 20, "Geladeira 1"),
    ("Iogurte Natural 170g", "Laticinios", "UN", Decimal("2.10"), Decimal("3.80"), 15, "Geladeira 1"),
    ("Queijo Mussarela 500g", "Laticinios", "KG", Decimal("18.00"), Decimal("29.90"), 5, "Geladeira 2"),
    ("Tomate", "Hortifruti", "KG", Decimal("4.50"), Decimal("7.90"), 10, "Hortifruti"),
    ("Banana Prata", "Hortifruti", "KG", Decimal("3.00"), Decimal("5.50"), 10, "Hortifruti"),
    ("Pao Frances", "Padaria", "KG", Decimal("6.00"), Decimal("12.00"), 5, "Padaria"),
    ("Presunto Fatiado 200g", "Frios", "UN", Decimal("5.50"), Decimal("9.90"), 8, "Geladeira 2"),
    ("Refrigerante Cola 2L", "Bebidas", "UN", Decimal("5.00"), Decimal("8.50"), 12, "Corredor 1"),
]

LOCALIZACOES_DEMO = ["Corredor 1", "Corredor 2", "Geladeira 1", "Geladeira 2", "Freezer", "Hortifruti", "Padaria", "Estoque"]


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existente = db.query(Empresa).filter(Empresa.nome_fantasia == "Mercado Sao Joao").first()
        if existente:
            print("Dados de demonstracao ja existem. Nada a fazer.")
            return

        empresa = Empresa(nome_fantasia="Mercado Sao Joao", razao_social="Mercado Sao Joao LTDA", email="contato@mercadosaojoao.com.br")
        db.add(empresa)
        db.flush()

        db.add(Configuracao(empresa_id=empresa.id, tipo_estabelecimento="mercado", onboarding_concluido=True, onboarding_etapa=9))

        admin = Usuario(
            empresa_id=empresa.id,
            nome="Administrador",
            email="admin@mercadosaojoao.com.br",
            senha_hash=hash_password("Senha123!"),
            perfil=PerfilUsuario.ADMINISTRADOR,
            cargo="Proprietario",
        )
        funcionario = Usuario(
            empresa_id=empresa.id,
            nome="Joao Funcionario",
            email="funcionario@mercadosaojoao.com.br",
            senha_hash=hash_password("Senha123!"),
            perfil=PerfilUsuario.FUNCIONARIO,
            cargo="Estoquista",
        )
        db.add_all([admin, funcionario])
        db.flush()

        categorias_por_nome = {}
        for nome in {p[1] for p in PRODUTOS_DEMO}:
            categoria = Categoria(id=uuid.uuid4(), empresa_id=empresa.id, nome=nome)
            db.add(categoria)
            categorias_por_nome[nome] = categoria

        localizacoes_por_nome = {}
        for nome in LOCALIZACOES_DEMO:
            localizacao = Localizacao(id=uuid.uuid4(), empresa_id=empresa.id, nome=nome, tipo="padrao")
            db.add(localizacao)
            localizacoes_por_nome[nome] = localizacao

        fornecedor = Fornecedor(
            id=uuid.uuid4(), empresa_id=empresa.id, nome="Distribuidora Central",
            razao_social="Distribuidora Central LTDA", telefone="(11) 4000-0000", email="vendas@distribuidoracentral.com.br",
        )
        db.add(fornecedor)
        db.flush()

        produtos = []
        for i, (nome, categoria, unidade, custo, venda, estoque_min, local) in enumerate(PRODUTOS_DEMO):
            produto = Produto(
                empresa_id=empresa.id,
                codigo_barras=f"789000000{i:03d}",
                nome=nome,
                categoria_id=categorias_por_nome[categoria].id,
                localizacao_id=localizacoes_por_nome[local].id,
                fornecedor_id=fornecedor.id,
                unidade_medida=unidade,
                preco_custo=custo,
                preco_venda=venda,
                estoque_minimo=estoque_min,
                estoque_atual=0,
            )
            db.add(produto)
            produtos.append(produto)
        db.flush()

        # Cada produto ganha 4 lotes: normal, atencao, vence-hoje, vencido -- cobre todos os status do dashboard.
        offsets_e_qtd = [(20, 30, StatusLote.ATIVO), (5, 15, StatusLote.PROXIMO_VENCIMENTO), (0, 12, StatusLote.PROXIMO_VENCIMENTO), (-5, 6, StatusLote.VENCIDO)]
        for idx, produto in enumerate(produtos):
            for lote_num, (dias, qtd, status) in enumerate(offsets_e_qtd, start=1):
                lote = Lote(
                    empresa_id=empresa.id,
                    produto_id=produto.id,
                    numero_lote=f"LT{idx:02d}{lote_num:02d}",
                    quantidade=qtd,
                    data_validade=today() + timedelta(days=dias),
                    data_entrada=today() - timedelta(days=30),
                    custo_unitario=produto.preco_custo,
                    status=status,
                )
                db.add(lote)
                produto.estoque_atual += qtd

        db.flush()

        # Perdas de exemplo nos ultimos dias, para o dashboard e relatorios terem dado.
        for i, produto in enumerate(produtos[:4]):
            qtd_perdida = 3 + i
            valor_unit = produto.preco_custo
            db.add(
                Perda(
                    empresa_id=empresa.id,
                    produto_id=produto.id,
                    quantidade=qtd_perdida,
                    motivo=MotivoPerda.PRODUTO_VENCIDO if i % 2 == 0 else MotivoPerda.PRODUTO_DANIFICADO,
                    valor_unitario=valor_unit,
                    valor_total=valor_total_perda(qtd_perdida, valor_unit),
                    data_perda=today() - timedelta(days=i * 3),
                    observacao="Perda registrada via seed de demonstracao.",
                    usuario_id=admin.id,
                )
            )

        db.commit()
        print("Dados de demonstracao criados com sucesso.")
        print("Empresa: Mercado Sao Joao")
        print("Login admin: admin@mercadosaojoao.com.br / Senha123!")
        print("Login funcionario: funcionario@mercadosaojoao.com.br / Senha123!")
    finally:
        db.close()


if __name__ == "__main__":
    run()
