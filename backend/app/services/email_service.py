import json
import logging
import urllib.error
import urllib.request

from app.config import get_settings

logger = logging.getLogger("valistock")
settings = get_settings()

RESEND_URL = "https://api.resend.com/emails"


def enviar_email(para: str, assunto: str, html: str, texto: str) -> bool:
    """Envia um e-mail transacional pelo Resend. Nunca levanta erro: quem chama (ex.: recuperacao de
    senha) nao pode revelar ao usuario se o envio falhou. Devolve True se o Resend aceitou."""
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY nao configurada; e-mail para %s nao foi enviado.", para)
        return False

    corpo = json.dumps({"from": settings.email_from, "to": [para], "subject": assunto, "html": html, "text": texto}).encode("utf-8")
    req = urllib.request.Request(
        RESEND_URL,
        data=corpo,
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
            # O Resend fica atras da Cloudflare, que recusa o User-Agent padrao do urllib.
            "User-Agent": "valistock-backend/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except urllib.error.HTTPError as exc:
        logger.error("Resend recusou o e-mail (%s): %s", exc.code, exc.read().decode("utf-8", "replace")[:300])
    except Exception:
        logger.exception("Falha ao chamar o Resend.")
    return False
