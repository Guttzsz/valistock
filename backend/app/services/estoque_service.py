from uuid import UUID

from sqlalchemy.orm import Session

from app.models.movimentacao_estoque import MovimentacaoEstoque, TipoMovimentacao
from app.models.produto import Produto


def ajustar_estoque(
    db: Session,
    produto: Produto,
    delta: int,
    tipo: TipoMovimentacao,
    usuario_id: UUID | None,
    lote_id: UUID | None = None,
    motivo: str | None = None,
) -> None:
    """Aplica `delta` ao estoque do produto (pode ser negativo) e registra o movimento para auditoria/rastreabilidade.
    Nunca altera estoque_atual silenciosamente fora desta funcao."""
    produto.estoque_atual = max(0, produto.estoque_atual + delta)

    db.add(
        MovimentacaoEstoque(
            empresa_id=produto.empresa_id,
            produto_id=produto.id,
            lote_id=lote_id,
            tipo=tipo,
            quantidade=abs(delta),
            estoque_resultante=produto.estoque_atual,
            motivo=motivo,
            usuario_id=usuario_id,
        )
    )
