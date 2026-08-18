from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.models.alerta import Alerta
from app.models.produto import Produto
from app.schemas.alerta import AlertaOut
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/api/alertas", tags=["alertas"])


@router.get("", response_model=list[AlertaOut])
def listar_alertas(
    lido: bool | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Alerta, Produto.nome)
        .join(Produto, Produto.id == Alerta.produto_id)
        .where(Alerta.empresa_id == current_user.empresa_id, Alerta.ignorado.is_(False))
    )
    if lido is not None:
        stmt = stmt.where(Alerta.lido == lido)
    stmt = stmt.order_by(Alerta.criado_em.desc())

    return [AlertaOut.from_alerta(alerta, produto_nome) for alerta, produto_nome in db.execute(stmt).all()]


def _get_alerta_da_empresa(db: Session, alerta_id: UUID, empresa_id: UUID) -> Alerta:
    alerta = db.scalar(select(Alerta).where(Alerta.id == alerta_id, Alerta.empresa_id == empresa_id))
    if alerta is None:
        raise NotFoundError("Alerta nao encontrado.")
    return alerta


@router.put("/{alerta_id}/ler", response_model=AlertaOut)
def marcar_como_lido(alerta_id: UUID, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    alerta = _get_alerta_da_empresa(db, alerta_id, current_user.empresa_id)
    alerta.lido = True
    db.commit()
    db.refresh(alerta)
    produto = db.get(Produto, alerta.produto_id)
    return AlertaOut.from_alerta(alerta, produto.nome if produto else "")


@router.put("/{alerta_id}/ignorar", status_code=204)
def ignorar_alerta(alerta_id: UUID, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    alerta = _get_alerta_da_empresa(db, alerta_id, current_user.empresa_id)
    alerta.ignorado = True
    alerta.lido = True
    db.commit()
    return None
