from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.models.lote import Lote, StatusLote
from app.models.produto import Produto
from app.schemas.lote import LoteCreate, LoteOut, LoteUpdate
from app.services.validade_service import status_validade
from app.utils.exceptions import NotFoundError, ValidationErrorApp
from app.utils.timezone import today

router = APIRouter(prefix="/api/lotes", tags=["lotes"])


def _get_lote_da_empresa(db: Session, lote_id: UUID, empresa_id: UUID) -> Lote:
    lote = db.scalar(select(Lote).where(Lote.id == lote_id, Lote.empresa_id == empresa_id))
    if lote is None:
        raise NotFoundError("Lote nao encontrado.")
    return lote


@router.get("", response_model=list[LoteOut])
def listar_lotes(
    produto_id: UUID | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Lote).where(Lote.empresa_id == current_user.empresa_id)
    if produto_id:
        stmt = stmt.where(Lote.produto_id == produto_id)
    stmt = stmt.order_by(Lote.data_validade)
    return db.scalars(stmt).all()


@router.post("", response_model=LoteOut, status_code=201)
def criar_lote(payload: LoteCreate, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    produto = db.scalar(select(Produto).where(Produto.id == payload.produto_id, Produto.empresa_id == current_user.empresa_id))
    if produto is None:
        raise NotFoundError("Produto nao encontrado.")

    data_entrada = payload.data_entrada or today()

    status = StatusLote.VENCIDO if status_validade(payload.data_validade) == "vencido" else StatusLote.ATIVO

    lote = Lote(
        empresa_id=current_user.empresa_id,
        produto_id=payload.produto_id,
        numero_lote=payload.numero_lote,
        quantidade=payload.quantidade,
        data_validade=payload.data_validade,
        data_entrada=data_entrada,
        custo_unitario=payload.custo_unitario,
        status=status,
    )
    db.add(lote)

    produto.estoque_atual += payload.quantidade

    db.commit()
    db.refresh(lote)
    return lote


@router.put("/{lote_id}", response_model=LoteOut)
def atualizar_lote(lote_id: UUID, payload: LoteUpdate, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    lote = _get_lote_da_empresa(db, lote_id, current_user.empresa_id)
    dados = payload.model_dump(exclude_unset=True)

    if "quantidade" in dados:
        produto = db.get(Produto, lote.produto_id)
        diferenca = dados["quantidade"] - lote.quantidade
        if produto.estoque_atual + diferenca < 0:
            raise ValidationErrorApp("Quantidade invalida.")
        produto.estoque_atual += diferenca

    for campo, valor in dados.items():
        setattr(lote, campo, valor)

    db.commit()
    db.refresh(lote)
    return lote


@router.delete("/{lote_id}", status_code=204)
def remover_lote(lote_id: UUID, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    lote = _get_lote_da_empresa(db, lote_id, current_user.empresa_id)
    produto = db.get(Produto, lote.produto_id)
    if produto is not None:
        produto.estoque_atual = max(0, produto.estoque_atual - lote.quantidade)
    db.delete(lote)
    db.commit()
    return None


@router.put("/{lote_id}/marcar-vendido", response_model=LoteOut)
def marcar_como_vendido(lote_id: UUID, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Ação rápida a partir de um alerta: dá baixa total no lote antes que vire prejuízo."""
    lote = _get_lote_da_empresa(db, lote_id, current_user.empresa_id)
    produto = db.get(Produto, lote.produto_id)
    if produto is not None:
        produto.estoque_atual = max(0, produto.estoque_atual - lote.quantidade)
    lote.status = StatusLote.ESGOTADO
    lote.quantidade = 0
    db.commit()
    db.refresh(lote)
    return lote
