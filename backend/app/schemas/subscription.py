from pydantic import BaseModel

from app.models.subscription import PlanoNome, StatusAssinatura


class SubscriptionOut(BaseModel):
    plano: PlanoNome
    status: StatusAssinatura
    limite_produtos: int | None
    limite_usuarios: int | None
