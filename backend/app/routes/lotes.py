from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user, require_permissao
from app.auth.permissions import Permissao
from app.database import get_db
from app.models.lote import Lote, StatusLote
from app.models.movimentacao_estoque import TipoMovimentacao
from app.models.produto import Produto
from app.schemas.lote import LoteCreate, LoteOut, LoteUpdate
from app.services.auditoria_service import registrar_auditoria
from app.services.estoque_service import ajustar_estoque
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
    current_user: CurrentUser = Depends(require_permissao(Permissao.LOTES_VISUALIZAR)),
    db: Session = Depends(get_db),
):
    stmt = select(Lote).where(Lote.empresa_id == current_user.empresa_id)
    if produto_id:
        stmt = stmt.where(Lote.produto_id == produto_id)
    stmt = stmt.order_by(Lote.data_validade)
    return db.scalars(stmt).all()


@router.post("", response_model=LoteOut, status_code=201)
def criar_lote(
    payload: LoteCreate,
    current_user: CurrentUser = Depends(require_permissao(Permissao.LOTES_CRIAR)),
    db: Session = Depends(get_db),
):
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
    db.flush()  # garante lote.id para a movimentacao de estoque

    ajustar_estoque(
        db, produto, payload.quantidade, TipoMovimentacao.ENTRADA, current_user.id,
        lote_id=lote.id, motivo=f"Entrada do lote {lote.numero_lote}",
    )
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "lote.criado", "lote", lote.id,
        f"{current_user.nome} cadastrou o lote {lote.numero_lote} de {produto.nome} ({payload.quantidade} un.).",
    )

    db.commit()
    db.refresh(lote)
    return lote


@router.put("/{lote_id}", response_model=LoteOut)
def atualizar_lote(
    lote_id: UUID,
    payload: LoteUpdate,
    current_user: CurrentUser = Depends(require_permissao(Permissao.LOTES_EDITAR)),
    db: Session = Depends(get_db),
):
    lote = _get_lote_da_empresa(db, lote_id, current_user.empresa_id)
    dados = payload.model_dump(exclude_unset=True)

    if "quantidade" in dados:
        produto = db.get(Produto, lote.produto_id)
        diferenca = dados["quantidade"] - lote.quantidade
        if produto.estoque_atual + diferenca < 0:
            raise ValidationErrorApp("Quantidade invalida.")
        if diferenca != 0:
            ajustar_estoque(
                db, produto, diferenca, TipoMovimentacao.AJUSTE, current_user.id,
                lote_id=lote.id, motivo=f"Ajuste manual do lote {lote.numero_lote}",
            )

    for campo, valor in dados.items():
        setattr(lote, campo, valor)

    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "lote.atualizado", "lote", lote.id, f"{current_user.nome} atualizou o lote {lote.numero_lote}.",
    )
    db.commit()
    db.refresh(lote)
    return lote


@router.delete("/{lote_id}", status_code=204)
def remover_lote(
    lote_id: UUID,
    current_user: CurrentUser = Depends(require_permissao(Permissao.LOTES_EDITAR)),
    db: Session = Depends(get_db),
):
    lote = _get_lote_da_empresa(db, lote_id, current_user.empresa_id)
    produto = db.get(Produto, lote.produto_id)
    if produto is not None and lote.quantidade > 0:
        ajustar_estoque(
            db, produto, -lote.quantidade, TipoMovimentacao.AJUSTE, current_user.id,
            lote_id=lote.id, motivo=f"Remocao do lote {lote.numero_lote}",
        )
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "lote.removido", "lote", lote.id, f"{current_user.nome} removeu o lote {lote.numero_lote}.",
    )
    db.delete(lote)
    db.commit()
    return None


@router.put("/{lote_id}/marcar-vendido", response_model=LoteOut)
def marcar_como_vendido(
    lote_id: UUID,
    current_user: CurrentUser = Depends(require_permissao(Permissao.LOTES_EDITAR)),
    db: Session = Depends(get_db),
):
    """Ação rápida a partir de um alerta: dá baixa total no lote antes que vire prejuízo."""
    lote = _get_lote_da_empresa(db, lote_id, current_user.empresa_id)
    produto = db.get(Produto, lote.produto_id)
    if produto is not None and lote.quantidade > 0:
        ajustar_estoque(
            db, produto, -lote.quantidade, TipoMovimentacao.VENDA, current_user.id,
            lote_id=lote.id, motivo=f"Lote {lote.numero_lote} marcado como vendido",
        )
    lote.status = StatusLote.ESGOTADO
    lote.quantidade = 0
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "lote.vendido", "lote", lote.id, f"{current_user.nome} marcou o lote {lote.numero_lote} como vendido.",
    )
    db.commit()
    db.refresh(lote)
    return lote
