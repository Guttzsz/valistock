import hashlib
import secrets
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.redefinicao_senha import RedefinicaoSenha
from app.models.usuario import Usuario
from app.services.email_service import enviar_email
from app.utils.timezone import now

settings = get_settings()

VALIDADE = timedelta(hours=1)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def invalidar_todos(db: Session, usuario_id) -> None:
    """Marca como usados todos os tokens ainda abertos do usuario. Nao commita."""
    db.execute(
        update(RedefinicaoSenha).where(RedefinicaoSenha.usuario_id == usuario_id, RedefinicaoSenha.usado_em.is_(None)).values(usado_em=now())
    )


def criar_token(db: Session, usuario: Usuario) -> str:
    """Cria um token novo e invalida os anteriores. Nao commita."""
    invalidar_todos(db, usuario.id)
    token = secrets.token_urlsafe(32)
    db.add(RedefinicaoSenha(usuario_id=usuario.id, token_hash=_hash(token), expira_em=now() + VALIDADE))
    return token


def buscar_valido(db: Session, token: str) -> RedefinicaoSenha | None:
    return db.scalar(
        select(RedefinicaoSenha).where(
            RedefinicaoSenha.token_hash == _hash(token),
            RedefinicaoSenha.usado_em.is_(None),
            RedefinicaoSenha.expira_em > now(),
        )
    )


def enviar_link_de_redefinicao(para: str, nome: str, token: str) -> bool:
    link = f"{settings.frontend_url}/templates/redefinir-senha.html?token={token}"
    primeiro_nome = nome.split()[0] if nome else ""
    texto = (
        f"Ola {primeiro_nome},\n\n"
        "Recebemos um pedido para redefinir a senha da sua conta no ValiStock.\n"
        f"Para criar uma senha nova, abra o link abaixo (valido por 1 hora):\n\n{link}\n\n"
        "Se voce nao fez esse pedido, ignore este e-mail: sua senha continua a mesma.\n\n"
        "ValiStock - Menos perdas. Mais lucro."
    )
    html = f"""<div style="font-family:Arial,Helvetica,sans-serif;max-width:480px;margin:0 auto;color:#1f2937;line-height:1.5">
  <h2 style="color:#15803d;margin:0 0 16px">ValiStock</h2>
  <p>Ola {primeiro_nome},</p>
  <p>Recebemos um pedido para redefinir a senha da sua conta. Clique no botao abaixo para criar uma senha nova. O link vale por <strong>1 hora</strong>.</p>
  <p style="margin:24px 0"><a href="{link}" style="background:#15803d;color:#ffffff;padding:12px 22px;border-radius:8px;text-decoration:none;font-weight:bold;display:inline-block">Criar nova senha</a></p>
  <p style="font-size:13px;color:#6b7280">Se o botao nao funcionar, copie e cole este endereco no navegador:<br>{link}</p>
  <p style="font-size:13px;color:#6b7280">Se voce nao fez esse pedido, ignore este e-mail: sua senha continua a mesma.</p>
</div>"""
    return enviar_email(para, "Redefinir sua senha do ValiStock", html, texto)
