import csv
import io
from datetime import timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, require_permissao
from app.auth.permissions import Permissao
from app.database import get_db
from app.models.categoria import Categoria
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
    current_user: CurrentUser = Depends(require_permissao(Permissao.RELATORIOS_VISUALIZAR)),
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
        select(func.coalesce(Categoria.nome, "Sem categoria"), func.sum(Perda.valor_total).label("total"))
        .join(Produto, Produto.id == Perda.produto_id)
        .outerjoin(Categoria, Categoria.id == Produto.categoria_id)
        .where(Perda.empresa_id == current_user.empresa_id, Perda.data_perda.between(inicio, fim))
        .group_by(Categoria.nome)
        .order_by(func.sum(Perda.valor_total).desc())
    ).all()

    return {
        "periodo": {"inicio": inicio.isoformat(), "fim": fim.isoformat()},
        "total_perdas": float(total),
        "perdas_por_dia": [{"data": data.isoformat(), "valor": float(valor)} for data, valor in por_dia],
        "produtos_mais_perdas": [{"produto": nome, "valor": float(total), "quantidade": qtd} for nome, total, qtd in produtos_ranking],
        "categorias_mais_perdas": [{"categoria": cat, "valor": float(total)} for cat, total in categorias_ranking],
    }


@router.get("/perdas/exportar")
def exportar_perdas_csv(
    periodo: str = Query(default="30dias"),
    data_inicio: str | None = None,
    data_fim: str | None = None,
    current_user: CurrentUser = Depends(require_permissao(Permissao.RELATORIOS_EXPORTAR)),
    db: Session = Depends(get_db),
):
    inicio, fim = _intervalo(periodo, data_inicio, data_fim)

    linhas = db.execute(
        select(Perda, Produto.nome)
        .join(Produto, Produto.id == Perda.produto_id)
        .where(Perda.empresa_id == current_user.empresa_id, Perda.data_perda.between(inicio, fim))
        .order_by(Perda.data_perda.desc())
    ).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["Data", "Produto", "Quantidade", "Motivo", "Valor unitario", "Valor total", "Observacao"])
    for perda, produto_nome in linhas:
        writer.writerow(
            [perda.data_perda.isoformat(), produto_nome, perda.quantidade, perda.motivo.value,
             str(perda.valor_unitario), str(perda.valor_total), perda.observacao or ""]
        )
    buffer.seek(0)

    nome_arquivo = f"perdas_{inicio.isoformat()}_a_{fim.isoformat()}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )


@router.get("/risco")
def relatorio_risco(current_user: CurrentUser = Depends(require_permissao(Permissao.RELATORIOS_VISUALIZAR)), db: Session = Depends(get_db)):
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
