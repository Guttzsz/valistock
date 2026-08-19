from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user, require_permissao
from app.auth.permissions import Permissao
from app.database import get_db
from app.models.categoria import Categoria
from app.models.fornecedor import Fornecedor
from app.models.localizacao import Localizacao
from app.models.produto import Produto
from app.schemas.produto import ProdutoCreate, ProdutoOut, ProdutoUpdate
from app.services.auditoria_service import registrar_auditoria
from app.services.plano_service import check_plan_limit
from app.utils.exceptions import ConflictError, NotFoundError, ValidationErrorApp

router = APIRouter(prefix="/api/produtos", tags=["produtos"])


def _out(produto: Produto) -> ProdutoOut:
    item = ProdutoOut.model_validate(produto)
    item.categoria_nome = produto.categoria.nome if produto.categoria else None
    item.fornecedor_nome = produto.fornecedor.nome if produto.fornecedor else None
    item.localizacao_nome = produto.localizacao.nome if produto.localizacao else None
    return item


def _get_produto_da_empresa(db: Session, produto_id: UUID, empresa_id: UUID) -> Produto:
    produto = db.scalar(select(Produto).where(Produto.id == produto_id, Produto.empresa_id == empresa_id))
    if produto is None:
        raise NotFoundError("Produto nao encontrado.")
    return produto


def _validar_referencias(db: Session, empresa_id: UUID, dados: dict) -> None:
    """Garante que categoria/fornecedor/localizacao informados pertencem a mesma empresa do usuario."""
    checagens = [
        ("categoria_id", Categoria, "Categoria nao encontrada."),
        ("fornecedor_id", Fornecedor, "Fornecedor nao encontrado."),
        ("localizacao_id", Localizacao, "Localizacao nao encontrada."),
    ]
    for campo, modelo, mensagem in checagens:
        valor = dados.get(campo)
        if valor is None:
            continue
        existe = db.scalar(select(modelo.id).where(modelo.id == valor, modelo.empresa_id == empresa_id))
        if existe is None:
            raise ValidationErrorApp(mensagem)


@router.get("", response_model=list[ProdutoOut])
def listar_produtos(
    q: str | None = Query(default=None, description="Busca por nome ou codigo de barras"),
    categoria_id: UUID | None = None,
    fornecedor_id: UUID | None = None,
    localizacao_id: UUID | None = None,
    current_user: CurrentUser = Depends(require_permissao(Permissao.PRODUTOS_VISUALIZAR)),
    db: Session = Depends(get_db),
):
    stmt = select(Produto).where(Produto.empresa_id == current_user.empresa_id)
    if q:
        termo = f"%{q}%"
        stmt = stmt.where(or_(Produto.nome.ilike(termo), Produto.codigo_barras.ilike(termo), Produto.marca.ilike(termo)))
    if categoria_id:
        stmt = stmt.where(Produto.categoria_id == categoria_id)
    if fornecedor_id:
        stmt = stmt.where(Produto.fornecedor_id == fornecedor_id)
    if localizacao_id:
        stmt = stmt.where(Produto.localizacao_id == localizacao_id)
    stmt = stmt.order_by(Produto.nome)
    return [_out(p) for p in db.scalars(stmt).all()]


@router.post("", response_model=ProdutoOut, status_code=201)
def criar_produto(
    payload: ProdutoCreate,
    current_user: CurrentUser = Depends(require_permissao(Permissao.PRODUTOS_CRIAR)),
    db: Session = Depends(get_db),
):
    check_plan_limit(db, current_user.empresa_id, "products")

    if payload.codigo_barras:
        existente = db.scalar(
            select(Produto).where(Produto.empresa_id == current_user.empresa_id, Produto.codigo_barras == payload.codigo_barras)
        )
        if existente is not None:
            raise ConflictError("Este codigo de barras ja esta cadastrado.")

    dados = payload.model_dump()
    _validar_referencias(db, current_user.empresa_id, dados)

    produto = Produto(empresa_id=current_user.empresa_id, **dados)
    db.add(produto)
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "produto.criado", "produto", produto.id, f"{current_user.nome} cadastrou o produto {produto.nome}.",
    )
    db.commit()
    db.refresh(produto)
    return _out(produto)


@router.get("/{produto_id}", response_model=ProdutoOut)
def obter_produto(
    produto_id: UUID,
    current_user: CurrentUser = Depends(require_permissao(Permissao.PRODUTOS_VISUALIZAR)),
    db: Session = Depends(get_db),
):
    return _out(_get_produto_da_empresa(db, produto_id, current_user.empresa_id))


@router.put("/{produto_id}", response_model=ProdutoOut)
def atualizar_produto(
    produto_id: UUID,
    payload: ProdutoUpdate,
    current_user: CurrentUser = Depends(require_permissao(Permissao.PRODUTOS_EDITAR)),
    db: Session = Depends(get_db),
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

    _validar_referencias(db, current_user.empresa_id, dados)

    for campo, valor in dados.items():
        setattr(produto, campo, valor)

    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "produto.atualizado", "produto", produto.id, f"{current_user.nome} atualizou o produto {produto.nome}.",
    )
    db.commit()
    db.refresh(produto)
    return _out(produto)


@router.delete("/{produto_id}", status_code=204)
def remover_produto(
    produto_id: UUID,
    current_user: CurrentUser = Depends(require_permissao(Permissao.PRODUTOS_EXCLUIR)),
    db: Session = Depends(get_db),
):
    produto = _get_produto_da_empresa(db, produto_id, current_user.empresa_id)
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "produto.removido", "produto", produto.id, f"{current_user.nome} removeu o produto {produto.nome}.",
    )
    db.delete(produto)
    db.commit()
    return None


@router.get("/buscar/codigo-barras/{codigo}", response_model=ProdutoOut | None)
def buscar_por_codigo_barras(
    codigo: str,
    current_user: CurrentUser = Depends(require_permissao(Permissao.PRODUTOS_VISUALIZAR)),
    db: Session = Depends(get_db),
):
    """Used by the barcode-scan flow: returns the product if it exists, or null so the frontend offers to register it."""
    produto = db.scalar(select(Produto).where(Produto.empresa_id == current_user.empresa_id, Produto.codigo_barras == codigo))
    return _out(produto) if produto else None
