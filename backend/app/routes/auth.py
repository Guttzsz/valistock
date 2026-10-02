import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.crypto import decrypt_secret, encrypt_secret, is_encrypted
from app.auth.dependencies import CurrentUser, get_current_user
from app.auth.jwt import create_access_token, create_mfa_challenge_token, decode_mfa_challenge_token
from app.auth.mfa import (
    consumir_codigo_backup,
    gerar_codigos_backup,
    gerar_otpauth_url,
    gerar_qr_code_base64,
    gerar_segredo,
    hash_codigos_backup,
    verificar_codigo_totp,
)
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
    LoginResponse,
    MfaDisableRequest,
    MfaEnableRequest,
    MfaEnableResponse,
    MfaSetupResponse,
    MfaVerifyRequest,
    RegisterRequest,
    TokenResponse,
    TrocarSenhaRequest,
    UsuarioMe,
)
from app.rate_limit import limiter
from app.services.auditoria_service import registrar_auditoria
from app.utils.exceptions import ConflictError, UnauthorizedError, ValidationErrorApp
from app.utils.timezone import now

logger = logging.getLogger("valistock")

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("5/minute")
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
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


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.scalar(select(Usuario).where(Usuario.email == payload.email))
    if usuario is None or not usuario.ativo or not verify_password(payload.senha, usuario.senha_hash):
        logger.warning("Tentativa de login invalida para %s", payload.email)
        if usuario is not None:
            registrar_auditoria(
                db, usuario.empresa_id, usuario.id, usuario.nome,
                "usuario.login_falhou", "seguranca", usuario.id, f"Tentativa de login falhou para {usuario.nome}.",
            )
            db.commit()
        raise UnauthorizedError("Email ou senha invalidos.")

    if usuario.mfa_enabled:
        challenge_token = create_mfa_challenge_token(usuario.id)
        return LoginResponse(mfa_required=True, challenge_token=challenge_token)

    usuario.ultimo_login = now()
    registrar_auditoria(
        db, usuario.empresa_id, usuario.id, usuario.nome,
        "usuario.login", "seguranca", usuario.id, f"{usuario.nome} entrou no sistema.",
    )
    db.commit()

    token = create_access_token(usuario.id, usuario.empresa_id, usuario.perfil.value)
    return LoginResponse(access_token=token, usuario=UsuarioMe.model_validate(usuario))


@router.post("/mfa/verify", response_model=TokenResponse)
@limiter.limit("10/minute")
def mfa_verify(request: Request, payload: MfaVerifyRequest, db: Session = Depends(get_db)):
    try:
        usuario_id = decode_mfa_challenge_token(payload.challenge_token)
    except ValueError as exc:
        raise UnauthorizedError(str(exc)) from exc

    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.ativo or not usuario.mfa_enabled:
        raise UnauthorizedError("Sessao de verificacao invalida.")

    codigo = payload.codigo.strip()
    segredo = decrypt_secret(usuario.mfa_secret)
    valido = verificar_codigo_totp(segredo, codigo)

    if not is_encrypted(usuario.mfa_secret):
        usuario.mfa_secret = encrypt_secret(segredo)

    if not valido:
        backup_atualizado = consumir_codigo_backup(usuario.mfa_backup_codes, codigo)
        if backup_atualizado is None:
            logger.warning("Codigo MFA invalido para usuario %s", usuario_id)
            registrar_auditoria(
                db, usuario.empresa_id, usuario.id, usuario.nome,
                "usuario.mfa_verificacao_falhou", "seguranca", usuario.id, f"Codigo de verificacao invalido para {usuario.nome}.",
            )
            db.commit()
            raise UnauthorizedError("Codigo de verificacao invalido.")
        usuario.mfa_backup_codes = backup_atualizado
        valido = True

    usuario.ultimo_login = now()
    registrar_auditoria(
        db, usuario.empresa_id, usuario.id, usuario.nome,
        "usuario.login", "seguranca", usuario.id, f"{usuario.nome} entrou no sistema (verificacao em duas etapas).",
    )
    db.commit()

    token = create_access_token(usuario.id, usuario.empresa_id, usuario.perfil.value)
    return TokenResponse(access_token=token, usuario=UsuarioMe.model_validate(usuario))


@router.post("/mfa/setup", response_model=MfaSetupResponse)
def mfa_setup(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    usuario = db.get(Usuario, current_user.id)
    if usuario.mfa_enabled:
        raise ConflictError("A autenticacao em duas etapas ja esta ativada.")

    segredo = gerar_segredo()
    usuario.mfa_secret = encrypt_secret(segredo)
    db.commit()

    otpauth_url = gerar_otpauth_url(segredo, usuario.email)
    return MfaSetupResponse(secret=segredo, otpauth_url=otpauth_url, qr_code_base64=gerar_qr_code_base64(otpauth_url))


@router.post("/mfa/enable", response_model=MfaEnableResponse)
def mfa_enable(payload: MfaEnableRequest, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    usuario = db.get(Usuario, current_user.id)
    if usuario.mfa_enabled:
        raise ConflictError("A autenticacao em duas etapas ja esta ativada.")
    if not usuario.mfa_secret:
        raise ValidationErrorApp("Inicie a configuracao antes de confirmar o codigo.")
    if not verificar_codigo_totp(decrypt_secret(usuario.mfa_secret), payload.codigo.strip()):
        raise ValidationErrorApp("Codigo invalido. Verifique o aplicativo autenticador e tente novamente.")

    codigos_backup = gerar_codigos_backup()
    usuario.mfa_enabled = True
    usuario.mfa_backup_codes = hash_codigos_backup(codigos_backup)
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "usuario.mfa_ativado", "seguranca", usuario.id, f"{current_user.nome} ativou a autenticacao em duas etapas.",
    )
    db.commit()
    return MfaEnableResponse(backup_codes=codigos_backup)


@router.post("/mfa/disable", status_code=204)
@limiter.limit("10/minute")
def mfa_disable(
    request: Request, payload: MfaDisableRequest, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    usuario = db.get(Usuario, current_user.id)
    if not verify_password(payload.senha, usuario.senha_hash):
        registrar_auditoria(
            db, current_user.empresa_id, current_user.id, current_user.nome,
            "usuario.mfa_desativacao_falhou", "seguranca", usuario.id,
            f"Tentativa de desativar a autenticacao em duas etapas com senha incorreta ({current_user.nome}).",
        )
        db.commit()
        raise ValidationErrorApp("Senha incorreta.")

    usuario.mfa_enabled = False
    usuario.mfa_secret = None
    usuario.mfa_backup_codes = None
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "usuario.mfa_desativado", "seguranca", usuario.id, f"{current_user.nome} desativou a autenticacao em duas etapas.",
    )
    db.commit()
    return None


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
@limiter.limit("10/minute")
def trocar_minha_senha(
    request: Request, payload: TrocarSenhaRequest, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    usuario = db.get(Usuario, current_user.id)
    if not verify_password(payload.senha_atual, usuario.senha_hash):
        registrar_auditoria(
            db, current_user.empresa_id, current_user.id, current_user.nome,
            "usuario.senha_alteracao_falhou", "seguranca", usuario.id,
            f"Tentativa de trocar a senha com a senha atual incorreta ({current_user.nome}).",
        )
        db.commit()
        raise ValidationErrorApp("Senha atual incorreta.")
    usuario.senha_hash = hash_password(payload.senha_nova)
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "usuario.senha_alterada", "seguranca", usuario.id, f"{current_user.nome} alterou a propria senha.",
    )
    db.commit()
    return None


@router.get("/permissoes")
def minhas_permissoes(current_user: CurrentUser = Depends(get_current_user)):
    """Lista as permissoes do usuario logado, para o frontend decidir o que mostrar/esconder.
    Isto e apenas cosmetico: a autorizacao real sempre acontece no backend, em cada rota."""
    return {"perfil": current_user.perfil.value, "permissoes": permissoes_do_perfil(current_user.perfil)}
