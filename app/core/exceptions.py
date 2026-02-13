from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    """Recurso não encontrado."""

    def __init__(self, detail: str = "Recurso não encontrado"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UnauthorizedException(HTTPException):
    """Token inválido ou ausente."""

    def __init__(self, detail: str = "Token de API inválido ou ausente"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(HTTPException):
    """Sem permissão para acessar o recurso."""

    def __init__(self, detail: str = "Sem permissão para acessar este recurso"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ValidationException(HTTPException):
    """Erro de validação de dados."""

    def __init__(self, detail: str = "Dados inválidos"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
        )


class ConflictException(HTTPException):
    """Conflito de dados (ex: duplicata)."""

    def __init__(self, detail: str = "Conflito de dados"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)
