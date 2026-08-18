from datetime import timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.models.lote import Lote, StatusLote
from app.models.perda import Perda
from app.models.produto import Produto
from app.services.financeiro_service import valor_em_risco
from app.utils.timezone import today

router = APIRouter(prefix="/api/relatorios", tags=["relatorios"])

PERIODOS = {"hoje": 0, "7dias": 7, "30dias": 30, "90dias": 90}


def _intervalo(periodo: str, data_inicio_custom, data_fim_custom):
    if periodo == "personalizado":
        return data_inicio_custom or today(), data_fim_custom or today()
    dias = PERIODOS.get(periodo, 30)
    return today() - timedelta(days=dias), today()


@router.get("/perdas")
def relatorio_perdas(
    periodo: str = Query(default="30dias"),
    data_inicio: str | None = None,
    data_fim: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inicio, fim = _intervalo(periodo, data_inicio, data_fim)

    total = db.scalar(
        select(func.coalesce(func.sum(Perda.valor_total), 0)).where(
            Perda.empresa_id == current_user.empresa_id, Perda.data_perda.between(inicio, fim)
        )
    ) or 0

    por_dia = db.execute(
        select(Perda.data_perda, func.sum(Perda.valor_total))
        .where(Perda.empresa_id == current_user.empresa_id, Perda.data_perda.between(inicio, fim))
        .group_by(Perda.data_perda)
        .order_by(Perda.data_perda)
    ).all()

    produtos_ranking = db.execute(
        select(Produto.nome, func.sum(Perda.valor_total).label("total"), func.sum(Perda.quantidade).label("quantidade"))
        .join(Produto, Produto.id == Perda.produto_id)
        .where(Perda.empresa_id == current_user.empresa_id, Perda.data_perda.between(inicio, fim))
        .group_by(Produto.nome)
        .order_by(func.sum(Perda.valor_total).desc())
        .limit(10)
    ).all()

    categorias_ranking = db.execute(
        select(Produto.categoria, func.sum(Perda.valor_total).label("total"))
        .join(Produto, Produto.id == Perda.produto_id)
        .where(Perda.empresa_id == current_user.empresa_id, Perda.data_perda.between(inicio, fim))
        .group_by(Produto.categoria)
        .order_by(func.sum(Perda.valor_total).desc())
    ).all()

    return {
        "periodo": {"inicio": inicio.isoformat(), "fim": fim.isoformat()},
        "total_perdas": float(total),
        "perdas_por_dia": [{"data": data.isoformat(), "valor": float(valor)} for data, valor in por_dia],
        "produtos_mais_perdas": [{"produto": nome, "valor": float(total), "quantidade": qtd} for nome, total, qtd in produtos_ranking],
        "categorias_mais_perdas": [{"categoria": cat or "Sem categoria", "valor": float(total)} for cat, total in categorias_ranking],
    }


@router.get("/risco")
def relatorio_risco(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    lotes = db.execute(
        select(Lote, Produto.nome)
        .join(Produto, Produto.id == Lote.produto_id)
        .where(
            Lote.empresa_id == current_user.empresa_id,
            Lote.status.in_([StatusLote.PROXIMO_VENCIMENTO, StatusLote.VENCIDO]),
        )
        .order_by(Lote.data_validade)
    ).all()

    itens = [
        {
            "produto": nome,
            "lote": lote.numero_lote,
            "quantidade": lote.quantidade,
            "data_validade": lote.data_validade.isoformat(),
            "valor_em_risco": float(valor_em_risco(lote.quantidade, lote.custo_unitario)),
            "status": lote.status.value,
        }
        for lote, nome in lotes
    ]

    return {"itens": itens, "total_em_risco": sum(item["valor_em_risco"] for item in itens)}
