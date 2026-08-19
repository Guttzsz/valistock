from uuid import UUID

from sqlalchemy.orm import Session

from app.models.auditoria import LogAuditoria


def registrar_auditoria(
    db: Session,
    empresa_id: UUID,
    usuario_id: UUID | None,
    usuario_nome: str | None,
    acao: str,
    entidade: str,
    entidade_id: UUID | None,
    descricao: str,
) -> None:
    """Registra uma acao no historico. Nao commita: participa da mesma transacao da operacao que a originou."""
    db.add(
        LogAuditoria(
            empresa_id=empresa_id,
            usuario_id=usuario_id,
            usuario_nome=usuario_nome,
            acao=acao,
            entidade=entidade,
            entidade_id=entidade_id,
            descricao=descricao,
        )
    )
