import json
import logging

from pywebpush import WebPushException, webpush
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.push_subscription import PushSubscription

logger = logging.getLogger("valistock")
settings = get_settings()


def enviar_push_para_empresa(db: Session, empresa_id, titulo: str, corpo: str, url: str = "/templates/alertas.html") -> None:
    if not settings.vapid_private_key:
        return  # push nao configurado neste ambiente (ex.: testes, dev local sem chave)

    subs = db.scalars(select(PushSubscription).where(PushSubscription.empresa_id == empresa_id)).all()
    if not subs:
        return

    payload = json.dumps({"titulo": titulo, "corpo": corpo, "url": url})
    inscricoes_mortas = []

    for sub in subs:
        try:
            webpush(
                subscription_info={"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}},
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": f"mailto:{settings.vapid_admin_email}"},
                ttl=3600,  # sem isso, o WNS (Edge/Chrome no Windows) rejeita com "Ttl value conflicts with X-WNS-Cache-Policy"
            )
        except WebPushException as e:
            status = e.response.status_code if e.response is not None else None
            if status in (404, 410):
                inscricoes_mortas.append(sub)
            else:
                logger.warning("Falha ao enviar push (status %s): %s", status, e)

    for sub in inscricoes_mortas:
        db.delete(sub)
    if inscricoes_mortas:
        db.commit()
