from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user
from app.auth.jwt import create_access_token
from app.auth.permissions import permissoes_do_perfil
from app.auth.security import hash_password, verify_password
from app.database import get_db
from app.models.configuracao import Configuracao
from app.models.empresa import Empresa
from app.models.usuario import PerfilUsuario, Usuario
from app.schemas.auth import (
    AtualizarAparenciaRequest,
    AtualizarPerfilRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    TrocarSenhaRequest,
    UsuarioMe,
)
from app.utils.exceptions import ConflictError, UnauthorizedError, ValidationErrorApp
from app.utils.timezone import now

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existente = db.scalar(select(Usuario).where(Usuario.email == payload.admin_email))
    if existente is not None:
        raise ConflictError("Este email ja esta cadastrado.")

    empresa = Empresa(nome_fantasia=payload.empresa_nome_fantasia, email=payload.empresa_email)
    db.add(empresa)
    db.flush()

    db.add(Configuracao(empresa_id=empresa.id))

    admin = Usuario(
        empresa_id=empresa.id,
        nome=payload.admin_nome,
        email=payload.admin_email,
        senha_hash=hash_password(payload.admin_senha),
        perfil=PerfilUsuario.ADMINISTRADOR,
        ultimo_login=now(),
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    token = create_access_token(admin.id, admin.empresa_id, admin.perfil.value)
    return TokenResponse(access_token=token, usuario=UsuarioMe.model_validate(admin))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.scalar(select(Usuario).where(Usuario.email == payload.email))
    if usuario is None or not usuario.ativo or not verify_password(payload.senha, usuario.senha_hash):
        raise UnauthorizedError("Email ou senha invalidos.")

    usuario.ultimo_login = now()
    db.commit()

    token = create_access_token(usuario.id, usuario.empresa_id, usuario.perfil.value)
    return TokenResponse(access_token=token, usuario=UsuarioMe.model_validate(usuario))


@router.post("/logout", status_code=204)
def logout(current_user: CurrentUser = Depends(get_current_user)):
    # Stateless JWT: logout is enforced client-side by discarding the token.
    return None


@router.get("/me", response_model=UsuarioMe)
def me(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    usuario = db.get(Usuario, current_user.id)
    return UsuarioMe.model_validate(usuario)


@router.put("/perfil", response_model=UsuarioMe)
def atualizar_meu_perfil(payload: AtualizarPerfilRequest, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    usuario = db.get(Usuario, current_user.id)
    usuario.nome = payload.nome
    db.commit()
    db.refresh(usuario)
    return UsuarioMe.model_validate(usuario)


@router.put("/aparencia", response_model=UsuarioMe)
def atualizar_minha_aparencia(payload: AtualizarAparenciaRequest, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    usuario = db.get(Usuario, current_user.id)
    usuario.theme = payload.theme
    usuario.accent_color = payload.accent_color
    db.commit()
    db.refresh(usuario)
    return UsuarioMe.model_validate(usuario)


@router.put("/senha", status_code=204)
def trocar_minha_senha(payload: TrocarSenhaRequest, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    usuario = db.get(Usuario, current_user.id)
    if not verify_password(payload.senha_atual, usuario.senha_hash):
        raise ValidationErrorApp("Senha atual incorreta.")
    usuario.senha_hash = hash_password(payload.senha_nova)
    db.commit()
    return None


@router.get("/permissoes")
def minhas_permissoes(current_user: CurrentUser = Depends(get_current_user)):
    """Lista as permissoes do usuario logado, para o frontend decidir o que mostrar/esconder.
    Isto e apenas cosmetico: a autorizacao real sempre acontece no backend, em cada rota."""
    return {"perfil": current_user.perfil.value, "permissoes": permissoes_do_perfil(current_user.perfil)}
