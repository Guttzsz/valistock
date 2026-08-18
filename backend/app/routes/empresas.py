from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user, require_admin
from app.database import get_db
from app.models.empresa import Empresa
from app.schemas.empresa import EmpresaOut, EmpresaUpdate

router = APIRouter(prefix="/api/empresas", tags=["empresas"])


@router.get("/atual", response_model=EmpresaOut)
def obter_empresa_atual(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.get(Empresa, current_user.empresa_id)


@router.put("/atual", response_model=EmpresaOut)
def atualizar_empresa_atual(payload: EmpresaUpdate, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    empresa = db.get(Empresa, current_user.empresa_id)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(empresa, campo, valor)
    db.commit()
    db.refresh(empresa)
    return empresa
