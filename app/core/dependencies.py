from typing import Annotated

from fastapi import Depends

from app.core.security import validate_api_token

# Dependency que extrai e valida o token, retornando o empresa_id
EmpresaId = Annotated[str, Depends(validate_api_token)]
