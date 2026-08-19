from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, require_permissao
from app.auth.permissions import Permissao
from app.database import get_db
from app.models.auditoria import LogAuditoria
from app.models.movimentacao_estoque import MovimentacaoEstoque
from app.models.produto import Produto
from app.models.usuario import Usuario
from app.schemas.auditoria import LogAuditoriaOut, MovimentacaoEstoqueOut

router = APIRouter(prefix="/api/historico", tags=["historico"])


@router.get("", response_model=list[LogAuditoriaOut])
def listar_historico(
    usuario_id: UUID | None = None,
    acao: str | None = None,
    entidade: str | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    limit: int = Query(default=100, le=500),
    current_user: CurrentUser = Depends(require_permissao(Permissao.AUDITORIA_VISUALIZAR)),
    db: Session = Depends(get_db),
):
    stmt = select(LogAuditoria).where(LogAuditoria.empresa_id == current_user.empresa_id)
    if usuario_id:
        stmt = stmt.where(LogAuditoria.usuario_id == usuario_id)
    if acao:
        stmt = stmt.where(LogAuditoria.acao == acao)
    if entidade:
        stmt = stmt.where(LogAuditoria.entidade == entidade)
    if data_inicio:
        stmt = stmt.where(LogAuditoria.criado_em >= data_inicio)
    if data_fim:
        stmt = stmt.where(LogAuditoria.criado_em <= data_fim)
    stmt = stmt.order_by(LogAuditoria.criado_em.desc()).limit(limit)
    return db.scalars(stmt).all()


@router.get("/estoque", response_model=list[MovimentacaoEstoqueOut])
def listar_movimentacoes_estoque(
    produto_id: UUID | None = None,
    limit: int = Query(default=100, le=500),
    current_user: CurrentUser = Depends(require_permissao(Permissao.AUDITORIA_VISUALIZAR)),
    db: Session = Depends(get_db),
):
    stmt = (
        select(MovimentacaoEstoque, Produto.nome, Usuario.nome)
        .join(Produto, Produto.id == MovimentacaoEstoque.produto_id)
        .outerjoin(Usuario, Usuario.id == MovimentacaoEstoque.usuario_id)
        .where(MovimentacaoEstoque.empresa_id == current_user.empresa_id)
    )
    if produto_id:
        stmt = stmt.where(MovimentacaoEstoque.produto_id == produto_id)
    stmt = stmt.order_by(MovimentacaoEstoque.criado_em.desc()).limit(limit)

    resultado = []
    for mov, produto_nome, usuario_nome in db.execute(stmt).all():
        resultado.append(
            MovimentacaoEstoqueOut(
                id=mov.id, produto_id=mov.produto_id, produto_nome=produto_nome, lote_id=mov.lote_id,
                tipo=mov.tipo.value, quantidade=mov.quantidade, estoque_resultante=mov.estoque_resultante,
                motivo=mov.motivo, usuario_nome=usuario_nome, criado_em=mov.criado_em,
            )
        )
    return resultado
