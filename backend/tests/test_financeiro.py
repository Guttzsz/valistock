from decimal import Decimal

from app.services.financeiro_service import valor_em_risco, valor_total_perda


def test_valor_em_risco_multiplica_quantidade_por_custo():
    assert valor_em_risco(50, Decimal("5.00")) == Decimal("250.00")


def test_valor_total_perda_multiplica_quantidade_por_valor_unitario():
    assert valor_total_perda(8, Decimal("5.00")) == Decimal("40.00")
