import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user, require_permissao
from app.auth.permissions import Permissao
from app.database import get_db
from app.models.localizacao import Localizacao
from app.schemas.localizacao import LocalizacaoCreate, LocalizacaoOut, LocalizacaoUpdate
from app.services.auditoria_service import registrar_auditoria
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/api/localizacoes", tags=["localizacoes"])


@router.get("", response_model=list[LocalizacaoOut])
def listar_localizacoes(
    incluir_inativas: bool = Query(default=False),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Localizacao).where(Localizacao.empresa_id == current_user.empresa_id).order_by(Localizacao.nome)
    if not incluir_inativas:
        stmt = stmt.where(Localizacao.ativo.is_(True))
    return db.scalars(stmt).all()


@router.post("", response_model=LocalizacaoOut, status_code=201)
def criar_localizacao(
    payload: LocalizacaoCreate,
    current_user: CurrentUser = Depends(require_permissao(Permissao.LOCALIZACOES_GERENCIAR)),
    db: Session = Depends(get_db),
):
    localizacao = Localizacao(id=uuid.uuid4(), empresa_id=current_user.empresa_id, **payload.model_dump())
    db.add(localizacao)
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "localizacao.criada", "localizacao", localizacao.id, f"{current_user.nome} criou o local {localizacao.nome}.",
    )
    db.commit()
    db.refresh(localizacao)
    return localizacao


def _get_localizacao_da_empresa(db: Session, localizacao_id: UUID, empresa_id: UUID) -> Localizacao:
    localizacao = db.scalar(select(Localizacao).where(Localizacao.id == localizacao_id, Localizacao.empresa_id == empresa_id))
    if localizacao is None:
        raise NotFoundError("Localizacao nao encontrada.")
    return localizacao


@router.put("/{localizacao_id}", response_model=LocalizacaoOut)
def atualizar_localizacao(
    localizacao_id: UUID,
    payload: LocalizacaoUpdate,
    current_user: CurrentUser = Depends(require_permissao(Permissao.LOCALIZACOES_GERENCIAR)),
    db: Session = Depends(get_db),
):
    localizacao = _get_localizacao_da_empresa(db, localizacao_id, current_user.empresa_id)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(localizacao, campo, valor)
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "localizacao.atualizada", "localizacao", localizacao.id, f"{current_user.nome} atualizou o local {localizacao.nome}.",
    )
    db.commit()
    db.refresh(localizacao)
    return localizacao


@router.delete("/{localizacao_id}", status_code=204)
def desativar_localizacao(
    localizacao_id: UUID,
    current_user: CurrentUser = Depends(require_permissao(Permissao.LOCALIZACOES_GERENCIAR)),
    db: Session = Depends(get_db),
):
    localizacao = _get_localizacao_da_empresa(db, localizacao_id, current_user.empresa_id)
    localizacao.ativo = False
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "localizacao.desativada", "localizacao", localizacao.id, f"{current_user.nome} desativou o local {localizacao.nome}.",
    )
    db.commit()
    return None
