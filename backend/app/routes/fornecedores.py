import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user, require_permissao
from app.auth.permissions import Permissao
from app.database import get_db
from app.models.fornecedor import Fornecedor
from app.models.produto import Produto
from app.schemas.fornecedor import FornecedorCreate, FornecedorOut, FornecedorUpdate
from app.services.auditoria_service import registrar_auditoria
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/api/fornecedores", tags=["fornecedores"])


def _out(fornecedor: Fornecedor, total_produtos: int) -> FornecedorOut:
    item = FornecedorOut.model_validate(fornecedor)
    item.total_produtos = total_produtos
    return item


@router.get("", response_model=list[FornecedorOut])
def listar_fornecedores(
    q: str | None = Query(default=None),
    incluir_inativos: bool = Query(default=False),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Fornecedor, func.count(Produto.id))
        .outerjoin(Produto, Produto.fornecedor_id == Fornecedor.id)
        .where(Fornecedor.empresa_id == current_user.empresa_id)
        .group_by(Fornecedor.id)
        .order_by(Fornecedor.nome)
    )
    if not incluir_inativos:
        stmt = stmt.where(Fornecedor.ativo.is_(True))
    if q:
        stmt = stmt.where(Fornecedor.nome.ilike(f"%{q}%"))
    return [_out(f, total) for f, total in db.execute(stmt).all()]


@router.post("", response_model=FornecedorOut, status_code=201)
def criar_fornecedor(
    payload: FornecedorCreate,
    current_user: CurrentUser = Depends(require_permissao(Permissao.FORNECEDORES_GERENCIAR)),
    db: Session = Depends(get_db),
):
    fornecedor = Fornecedor(id=uuid.uuid4(), empresa_id=current_user.empresa_id, **payload.model_dump())
    db.add(fornecedor)
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "fornecedor.criado", "fornecedor", fornecedor.id, f"{current_user.nome} cadastrou o fornecedor {fornecedor.nome}.",
    )
    db.commit()
    db.refresh(fornecedor)
    return _out(fornecedor, 0)


def _get_fornecedor_da_empresa(db: Session, fornecedor_id: UUID, empresa_id: UUID) -> Fornecedor:
    fornecedor = db.scalar(select(Fornecedor).where(Fornecedor.id == fornecedor_id, Fornecedor.empresa_id == empresa_id))
    if fornecedor is None:
        raise NotFoundError("Fornecedor nao encontrado.")
    return fornecedor


@router.put("/{fornecedor_id}", response_model=FornecedorOut)
def atualizar_fornecedor(
    fornecedor_id: UUID,
    payload: FornecedorUpdate,
    current_user: CurrentUser = Depends(require_permissao(Permissao.FORNECEDORES_GERENCIAR)),
    db: Session = Depends(get_db),
):
    fornecedor = _get_fornecedor_da_empresa(db, fornecedor_id, current_user.empresa_id)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(fornecedor, campo, valor)

    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "fornecedor.atualizado", "fornecedor", fornecedor.id, f"{current_user.nome} atualizou o fornecedor {fornecedor.nome}.",
    )
    db.commit()
    db.refresh(fornecedor)
    total = db.scalar(select(func.count()).select_from(Produto).where(Produto.fornecedor_id == fornecedor.id)) or 0
    return _out(fornecedor, total)


@router.delete("/{fornecedor_id}", status_code=204)
def desativar_fornecedor(
    fornecedor_id: UUID,
    current_user: CurrentUser = Depends(require_permissao(Permissao.FORNECEDORES_GERENCIAR)),
    db: Session = Depends(get_db),
):
    fornecedor = _get_fornecedor_da_empresa(db, fornecedor_id, current_user.empresa_id)
    fornecedor.ativo = False
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "fornecedor.desativado", "fornecedor", fornecedor.id, f"{current_user.nome} desativou o fornecedor {fornecedor.nome}.",
    )
    db.commit()
    return None
