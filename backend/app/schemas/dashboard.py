from decimal import Decimal

from pydantic import BaseModel


class DashboardOut(BaseModel):
    produtos_cadastrados: int
    lotes_proximos_vencimento: int
    lotes_vencidos: int
    valor_em_risco: Decimal
    perdas_do_mes: Decimal
    economia_potencial: Decimal
