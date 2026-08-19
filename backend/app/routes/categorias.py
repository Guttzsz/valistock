import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user, require_permissao
from app.auth.permissions import Permissao
from app.database import get_db
from app.models.categoria import Categoria
from app.models.produto import Produto
from app.schemas.categoria import CategoriaCreate, CategoriaOut, CategoriaUpdate
from app.services.auditoria_service import registrar_auditoria
from app.utils.exceptions import ConflictError, NotFoundError

router = APIRouter(prefix="/api/categorias", tags=["categorias"])


def _out(categoria: Categoria, total_produtos: int) -> CategoriaOut:
    item = CategoriaOut.model_validate(categoria)
    item.total_produtos = total_produtos
    return item


@router.get("", response_model=list[CategoriaOut])
def listar_categorias(
    q: str | None = Query(default=None),
    incluir_inativas: bool = Query(default=False),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Categoria, func.count(Produto.id))
        .outerjoin(Produto, Produto.categoria_id == Categoria.id)
        .where(Categoria.empresa_id == current_user.empresa_id)
        .group_by(Categoria.id)
        .order_by(Categoria.nome)
    )
    if not incluir_inativas:
        stmt = stmt.where(Categoria.ativo.is_(True))
    if q:
        stmt = stmt.where(Categoria.nome.ilike(f"%{q}%"))
    return [_out(categoria, total) for categoria, total in db.execute(stmt).all()]


@router.post("", response_model=CategoriaOut, status_code=201)
def criar_categoria(
    payload: CategoriaCreate,
    current_user: CurrentUser = Depends(require_permissao(Permissao.CATEGORIAS_GERENCIAR)),
    db: Session = Depends(get_db),
):
    existente = db.scalar(select(Categoria).where(Categoria.empresa_id == current_user.empresa_id, Categoria.nome == payload.nome))
    if existente is not None:
        raise ConflictError("Ja existe uma categoria com este nome.")

    categoria = Categoria(id=uuid.uuid4(), empresa_id=current_user.empresa_id, **payload.model_dump())
    db.add(categoria)
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "categoria.criada", "categoria", categoria.id, f"{current_user.nome} criou a categoria {categoria.nome}.",
    )
    db.commit()
    db.refresh(categoria)
    return _out(categoria, 0)


def _get_categoria_da_empresa(db: Session, categoria_id: UUID, empresa_id: UUID) -> Categoria:
    categoria = db.scalar(select(Categoria).where(Categoria.id == categoria_id, Categoria.empresa_id == empresa_id))
    if categoria is None:
        raise NotFoundError("Categoria nao encontrada.")
    return categoria


@router.put("/{categoria_id}", response_model=CategoriaOut)
def atualizar_categoria(
    categoria_id: UUID,
    payload: CategoriaUpdate,
    current_user: CurrentUser = Depends(require_permissao(Permissao.CATEGORIAS_GERENCIAR)),
    db: Session = Depends(get_db),
):
    categoria = _get_categoria_da_empresa(db, categoria_id, current_user.empresa_id)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(categoria, campo, valor)

    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "categoria.atualizada", "categoria", categoria.id, f"{current_user.nome} atualizou a categoria {categoria.nome}.",
    )
    db.commit()
    db.refresh(categoria)
    total = db.scalar(select(func.count()).select_from(Produto).where(Produto.categoria_id == categoria.id)) or 0
    return _out(categoria, total)


@router.delete("/{categoria_id}", status_code=204)
def desativar_categoria(
    categoria_id: UUID,
    current_user: CurrentUser = Depends(require_permissao(Permissao.CATEGORIAS_GERENCIAR)),
    db: Session = Depends(get_db),
):
    """Desativa (soft-delete) em vez de excluir, para preservar o historico de produtos ja associados."""
    categoria = _get_categoria_da_empresa(db, categoria_id, current_user.empresa_id)
    categoria.ativo = False
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "categoria.desativada", "categoria", categoria.id, f"{current_user.nome} desativou a categoria {categoria.nome}.",
    )
    db.commit()
    return None
