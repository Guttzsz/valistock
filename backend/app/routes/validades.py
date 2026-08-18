from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.models.lote import Lote, StatusLote
from app.models.produto import Produto
from app.schemas.lote import ValidadeOut
from app.services.financeiro_service import valor_em_risco
from app.services.validade_service import dias_restantes, status_validade

router = APIRouter(prefix="/api/validades", tags=["validades"])


@router.get("", response_model=list[ValidadeOut])
def listar_validades(
    status: str | None = Query(default=None, description="normal, atencao, urgente, vence_hoje, vencido"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Lote, Produto)
        .join(Produto, Produto.id == Lote.produto_id)
        .where(Lote.empresa_id == current_user.empresa_id, Lote.status != StatusLote.ESGOTADO, Lote.status != StatusLote.PERDIDO)
        .order_by(Lote.data_validade)
    )
    linhas = db.execute(stmt).all()

    resultado = []
    for lote, produto in linhas:
        status_atual = status_validade(lote.data_validade)
        if status and status != status_atual:
            continue
        resultado.append(
            ValidadeOut(
                lote_id=lote.id,
                produto_id=produto.id,
                produto_nome=produto.nome,
                codigo_barras=produto.codigo_barras,
                numero_lote=lote.numero_lote,
                quantidade=lote.quantidade,
                data_validade=lote.data_validade,
                dias_restantes=dias_restantes(lote.data_validade),
                valor_em_risco=valor_em_risco(lote.quantidade, lote.custo_unitario),
                status=status_atual,
            )
        )
    return resultado
