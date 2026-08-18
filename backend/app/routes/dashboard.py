from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.models.lote import Lote, StatusLote
from app.models.perda import Perda
from app.models.produto import Produto
from app.schemas.dashboard import DashboardOut
from app.utils.timezone import today

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def obter_dashboard(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    empresa_id = current_user.empresa_id

    produtos_cadastrados = db.scalar(
        select(func.count()).select_from(Produto).where(Produto.empresa_id == empresa_id, Produto.ativo.is_(True))
    ) or 0

    lotes_proximos = db.scalar(
        select(func.count()).select_from(Lote).where(Lote.empresa_id == empresa_id, Lote.status == StatusLote.PROXIMO_VENCIMENTO)
    ) or 0

    lotes_vencidos = db.scalar(
        select(func.count()).select_from(Lote).where(Lote.empresa_id == empresa_id, Lote.status == StatusLote.VENCIDO)
    ) or 0

    valor_risco = db.scalar(
        select(func.coalesce(func.sum(Lote.quantidade * Lote.custo_unitario), 0)).where(
            Lote.empresa_id == empresa_id,
            Lote.status.in_([StatusLote.PROXIMO_VENCIMENTO, StatusLote.VENCIDO]),
        )
    ) or Decimal(0)

    inicio_mes = today().replace(day=1)
    perdas_mes = db.scalar(
        select(func.coalesce(func.sum(Perda.valor_total), 0)).where(Perda.empresa_id == empresa_id, Perda.data_perda >= inicio_mes)
    ) or Decimal(0)

    # Economia potencial: metade do valor hoje em risco de vencimento, como estimativa de
    # quanto poderia ser recuperado com desconto/promocao antes de virar perda total.
    economia_potencial = Decimal(valor_risco) * Decimal("0.5")

    return DashboardOut(
        produtos_cadastrados=produtos_cadastrados,
        lotes_proximos_vencimento=lotes_proximos,
        lotes_vencidos=lotes_vencidos,
        valor_em_risco=Decimal(valor_risco),
        perdas_do_mes=Decimal(perdas_mes),
        economia_potencial=economia_potencial,
    )
