from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.models.produto import Produto
from app.schemas.produto import ProdutoCreate, ProdutoOut, ProdutoUpdate
from app.services.plano_service import check_plan_limit
from app.utils.exceptions import ConflictError, NotFoundError

router = APIRouter(prefix="/api/produtos", tags=["produtos"])


def _get_produto_da_empresa(db: Session, produto_id: UUID, empresa_id: UUID) -> Produto:
    produto = db.scalar(select(Produto).where(Produto.id == produto_id, Produto.empresa_id == empresa_id))
    if produto is None:
        raise NotFoundError("Produto nao encontrado.")
    return produto


@router.get("", response_model=list[ProdutoOut])
def listar_produtos(
    q: str | None = Query(default=None, description="Busca por nome ou codigo de barras"),
    categoria: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Produto).where(Produto.empresa_id == current_user.empresa_id)
    if q:
        termo = f"%{q}%"
        stmt = stmt.where(or_(Produto.nome.ilike(termo), Produto.codigo_barras.ilike(termo)))
    if categoria:
        stmt = stmt.where(Produto.categoria == categoria)
    stmt = stmt.order_by(Produto.nome)
    return db.scalars(stmt).all()


@router.post("", response_model=ProdutoOut, status_code=201)
def criar_produto(payload: ProdutoCreate, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    check_plan_limit(db, current_user.empresa_id, "products")

    if payload.codigo_barras:
        existente = db.scalar(
            select(Produto).where(Produto.empresa_id == current_user.empresa_id, Produto.codigo_barras == payload.codigo_barras)
        )
        if existente is not None:
            raise ConflictError("Este codigo de barras ja esta cadastrado.")

    produto = Produto(empresa_id=current_user.empresa_id, **payload.model_dump())
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


@router.get("/{produto_id}", response_model=ProdutoOut)
def obter_produto(produto_id: UUID, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_produto_da_empresa(db, produto_id, current_user.empresa_id)


@router.put("/{produto_id}", response_model=ProdutoOut)
def atualizar_produto(
    produto_id: UUID, payload: ProdutoUpdate, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    produto = _get_produto_da_empresa(db, produto_id, current_user.empresa_id)

    dados = payload.model_dump(exclude_unset=True)
    if "codigo_barras" in dados and dados["codigo_barras"]:
        existente = db.scalar(
            select(Produto).where(
                Produto.empresa_id == current_user.empresa_id,
                Produto.codigo_barras == dados["codigo_barras"],
                Produto.id != produto_id,
            )
        )
        if existente is not None:
            raise ConflictError("Este codigo de barras ja esta cadastrado.")

    for campo, valor in dados.items():
        setattr(produto, campo, valor)

    db.commit()
    db.refresh(produto)
    return produto


@router.delete("/{produto_id}", status_code=204)
def remover_produto(produto_id: UUID, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    produto = _get_produto_da_empresa(db, produto_id, current_user.empresa_id)
    db.delete(produto)
    db.commit()
    return None


@router.get("/buscar/codigo-barras/{codigo}", response_model=ProdutoOut | None)
def buscar_por_codigo_barras(codigo: str, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Used by the barcode-scan flow: returns the product if it exists, or null so the frontend offers to register it."""
    return db.scalar(select(Produto).where(Produto.empresa_id == current_user.empresa_id, Produto.codigo_barras == codigo))
