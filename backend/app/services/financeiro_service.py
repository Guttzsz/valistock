from decimal import Decimal


def valor_em_risco(quantidade: int, custo_unitario: Decimal) -> Decimal:
    return Decimal(quantidade) * custo_unitario


def valor_total_perda(quantidade: int, valor_unitario: Decimal) -> Decimal:
    return Decimal(quantidade) * valor_unitario
