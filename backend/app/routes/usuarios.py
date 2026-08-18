from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user, require_admin
from app.auth.security import hash_password
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.services.plano_service import check_plan_limit
from app.utils.exceptions import ConflictError, NotFoundError

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])


@router.get("", response_model=list[UsuarioOut])
def listar_usuarios(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(Usuario).where(Usuario.empresa_id == current_user.empresa_id).order_by(Usuario.nome)
    return db.scalars(stmt).all()


@router.post("", response_model=UsuarioOut, status_code=201)
def criar_usuario(payload: UsuarioCreate, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    check_plan_limit(db, current_user.empresa_id, "users")

    existente = db.scalar(select(Usuario).where(Usuario.email == payload.email))
    if existente is not None:
        raise ConflictError("Este email ja esta cadastrado.")

    usuario = Usuario(
        empresa_id=current_user.empresa_id,
        nome=payload.nome,
        email=payload.email,
        senha_hash=hash_password(payload.senha),
        cargo=payload.cargo,
        perfil=payload.perfil,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.put("/{usuario_id}", response_model=UsuarioOut)
def atualizar_usuario(
    usuario_id: UUID, payload: UsuarioUpdate, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
):
    usuario = db.scalar(select(Usuario).where(Usuario.id == usuario_id, Usuario.empresa_id == current_user.empresa_id))
    if usuario is None:
        raise NotFoundError("Usuario nao encontrado.")

    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(usuario, campo, valor)

    db.commit()
    db.refresh(usuario)
    return usuario


@router.delete("/{usuario_id}", status_code=204)
def remover_usuario(usuario_id: UUID, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    usuario = db.scalar(select(Usuario).where(Usuario.id == usuario_id, Usuario.empresa_id == current_user.empresa_id))
    if usuario is None:
        raise NotFoundError("Usuario nao encontrado.")
    db.delete(usuario)
    db.commit()
    return None
