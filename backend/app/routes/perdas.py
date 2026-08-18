from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.models.lote import Lote, StatusLote
from app.models.perda import Perda
from app.models.produto import Produto
from app.models.usuario import Usuario
from app.schemas.perda import PerdaComProduto, PerdaCreate, PerdaOut
from app.services.financeiro_service import valor_total_perda
from app.utils.exceptions import NotFoundError, ValidationErrorApp

router = APIRouter(prefix="/api/perdas", tags=["perdas"])


@router.get("", response_model=list[PerdaComProduto])
def listar_perdas(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    produto_id: UUID | None = None,
    motivo: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Perda, Produto.nome, Usuario.nome)
        .join(Produto, Produto.id == Perda.produto_id)
        .outerjoin(Usuario, Usuario.id == Perda.usuario_id)
        .where(Perda.empresa_id == current_user.empresa_id)
    )
    if data_inicio:
        stmt = stmt.where(Perda.data_perda >= data_inicio)
    if data_fim:
        stmt = stmt.where(Perda.data_perda <= data_fim)
    if produto_id:
        stmt = stmt.where(Perda.produto_id == produto_id)
    if motivo:
        stmt = stmt.where(Perda.motivo == motivo)
    stmt = stmt.order_by(Perda.data_perda.desc())

    resultado = []
    for perda, produto_nome, usuario_nome in db.execute(stmt).all():
        item = PerdaComProduto(**PerdaOut.model_validate(perda).model_dump(), produto_nome=produto_nome, usuario_nome=usuario_nome)
        resultado.append(item)
    return resultado


@router.post("", response_model=PerdaComProduto, status_code=201)
def registrar_perda(payload: PerdaCreate, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    produto = db.scalar(select(Produto).where(Produto.id == payload.produto_id, Produto.empresa_id == current_user.empresa_id))
    if produto is None:
        raise NotFoundError("Produto nao encontrado.")

    lote = None
    if payload.lote_id:
        lote = db.scalar(select(Lote).where(Lote.id == payload.lote_id, Lote.empresa_id == current_user.empresa_id))
        if lote is None:
            raise NotFoundError("Lote nao encontrado.")
        if payload.quantidade > lote.quantidade:
            raise ValidationErrorApp("Quantidade invalida: maior que a quantidade disponivel no lote.")

    custo_unitario = lote.custo_unitario if lote else produto.preco_custo
    valor_total = valor_total_perda(payload.quantidade, custo_unitario)

    perda = Perda(
        empresa_id=current_user.empresa_id,
        produto_id=payload.produto_id,
        lote_id=payload.lote_id,
        quantidade=payload.quantidade,
        motivo=payload.motivo,
        valor_unitario=custo_unitario,
        valor_total=valor_total,
        observacao=payload.observacao,
        usuario_id=current_user.id,
    )
    db.add(perda)

    produto.estoque_atual = max(0, produto.estoque_atual - payload.quantidade)
    if lote:
        lote.quantidade -= payload.quantidade
        if lote.quantidade == 0:
            lote.status = StatusLote.PERDIDO

    db.commit()
    db.refresh(perda)

    return PerdaComProduto(**PerdaOut.model_validate(perda).model_dump(), produto_nome=produto.nome, usuario_nome=current_user.nome)
