from fastapi import HTTPException, status


class AppError(HTTPException):
    """Base application error with a user-friendly message (never leaks internals)."""

    def __init__(self, status_code: int, message: str):
        super().__init__(status_code=status_code, detail=message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Registro nao encontrado."):
        super().__init__(status.HTTP_404_NOT_FOUND, message)


class ConflictError(AppError):
    def __init__(self, message: str = "Este registro ja existe."):
        super().__init__(status.HTTP_409_CONFLICT, message)


class ValidationErrorApp(AppError):
    def __init__(self, message: str = "Dados invalidos."):
        super().__init__(422, message)


class PermissionDeniedError(AppError):
    def __init__(self, message: str = "Voce nao possui permissao para realizar esta acao."):
        super().__init__(status.HTTP_403_FORBIDDEN, message)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Credenciais invalidas."):
        super().__init__(status.HTTP_401_UNAUTHORIZED, message)


class PlanLimitError(AppError):
    def __init__(self, message: str = "Limite do seu plano atingido."):
        super().__init__(status.HTTP_402_PAYMENT_REQUIRED, message)
