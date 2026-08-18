from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.models.subscription import StatusAssinatura, Subscription
from app.schemas.subscription import SubscriptionOut
from app.services.plano_service import LIMITES, get_plano_atual

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


@router.get("/atual", response_model=SubscriptionOut)
def obter_assinatura_atual(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    plano = get_plano_atual(db, current_user.empresa_id)
    sub = db.scalar(select(Subscription).where(Subscription.empresa_id == current_user.empresa_id))
    status = sub.status if sub else StatusAssinatura.ACTIVE
    limites = LIMITES[plano]
    return SubscriptionOut(plano=plano, status=status, limite_produtos=limites["products"], limite_usuarios=limites["users"])
