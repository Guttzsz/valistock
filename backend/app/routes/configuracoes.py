from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user, require_admin
from app.database import get_db
from app.models.configuracao import Configuracao
from app.schemas.configuracao import ConfiguracaoOut, ConfiguracaoUpdate

router = APIRouter(prefix="/api/configuracoes", tags=["configuracoes"])


def _get_or_create(db: Session, empresa_id) -> Configuracao:
    config = db.scalar(select(Configuracao).where(Configuracao.empresa_id == empresa_id))
    if config is None:
        config = Configuracao(empresa_id=empresa_id)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.get("", response_model=ConfiguracaoOut)
def obter_configuracoes(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_or_create(db, current_user.empresa_id)


@router.put("", response_model=ConfiguracaoOut)
def atualizar_configuracoes(payload: ConfiguracaoUpdate, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    config = _get_or_create(db, current_user.empresa_id)
    config.dias_alerta_1 = payload.dias_alerta_1
    config.dias_alerta_2 = payload.dias_alerta_2
    config.dias_alerta_3 = payload.dias_alerta_3
    db.commit()
    db.refresh(config)
    return config
