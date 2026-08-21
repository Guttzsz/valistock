from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.push_subscription import PushSubscription
from app.schemas.push import PushSubscriptionIn, PushUnsubscribeIn, VapidPublicKeyOut

settings = get_settings()

router = APIRouter(prefix="/api/push", tags=["push"])


@router.get("/chave-publica", response_model=VapidPublicKeyOut)
def obter_chave_publica():
    return VapidPublicKeyOut(chave=settings.vapid_public_key)


@router.post("/inscrever", status_code=204)
def inscrever(payload: PushSubscriptionIn, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    existente = db.scalar(select(PushSubscription).where(PushSubscription.endpoint == payload.endpoint))
    if existente is not None:
        existente.usuario_id = current_user.id
        existente.empresa_id = current_user.empresa_id
        existente.p256dh = payload.keys.p256dh
        existente.auth = payload.keys.auth
    else:
        db.add(
            PushSubscription(
                empresa_id=current_user.empresa_id,
                usuario_id=current_user.id,
                endpoint=payload.endpoint,
                p256dh=payload.keys.p256dh,
                auth=payload.keys.auth,
            )
        )
    db.commit()
    return None


@router.delete("/inscrever", status_code=204)
def desinscrever(payload: PushUnsubscribeIn, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    existente = db.scalar(
        select(PushSubscription).where(PushSubscription.endpoint == payload.endpoint, PushSubscription.usuario_id == current_user.id)
    )
    if existente is not None:
        db.delete(existente)
        db.commit()
    return None
