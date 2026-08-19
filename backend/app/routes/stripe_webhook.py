import logging

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.services.webhook_service import processar_evento

logger = logging.getLogger("valistock")
settings = get_settings()

router = APIRouter(prefix="/api/stripe", tags=["stripe"])


@router.post("/webhook", status_code=200)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    payload = await request.body()

    if not settings.stripe_webhook_secret:
        logger.error("STRIPE_WEBHOOK_SECRET nao configurado; recusando webhook.")
        raise HTTPException(status_code=500, detail="Webhook nao configurado.")

    try:
        event = stripe.Webhook.construct_event(payload, stripe_signature, settings.stripe_webhook_secret)
    except (ValueError, stripe.SignatureVerificationError) as exc:
        logger.warning("Webhook Stripe com assinatura invalida: %s", exc)
        raise HTTPException(status_code=400, detail="Assinatura invalida.") from exc

    processar_evento(db, event)

    return {"recebido": True}
