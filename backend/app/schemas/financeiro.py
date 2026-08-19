from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.models.fatura import StatusFatura
from app.models.subscription import PlanoNome, StatusAssinatura


class FinanceiroDashboardOut(BaseModel):
    receita_mensal: Decimal
    receita_anual: Decimal
    mrr: Decimal
    arr: Decimal
    assinaturas_ativas: int
    clientes_pagantes: int
    trials: int
    cancelamentos_periodo: int
    inadimplencia: int
    arpu: Decimal | None  # None = dados insuficientes (nenhum cliente pagante ainda)


class ReceitaPorMes(BaseModel):
    mes: str  # "2026-08"
    receita: Decimal


class ReceitaPorPlano(BaseModel):
    plano: PlanoNome
    quantidade: int
    receita_mensal: Decimal
    percentual: Decimal


class AssinaturaAdminOut(BaseModel):
    empresa_id: UUID
    empresa_nome: str
    plano: PlanoNome
    status: StatusAssinatura
    valor_mensal: Decimal
    data_inicio: date | None
    periodo_atual_fim: date | None
    stripe_customer_id: str | None
    stripe_subscription_id: str | None


class PagamentoAdminOut(BaseModel):
    id: UUID
    empresa_nome: str
    numero: str | None
    valor_total: Decimal
    status: StatusFatura
    criado_em: datetime
    url_fatura: str | None
