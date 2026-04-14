import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from fastapi import Header, HTTPException, Depends

# Esta clave debe ser la misma que usaste en el login
SECRET_KEY = "tu_clave_secreta_aqui"

# valida token y verifica que el usuario este activo

def verificar_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail={"error": {"code": "NO_TOKEN", "message": "Token de autenticación requerido"}})
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail={"error": {"code": "INVALID_TOKEN", "message": "Formato de token inválido"}})

    token = parts[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail={"error": {"code": "TOKEN_EXPIRED", "message": "El token expiró"}})
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail={"error": {"code": "INVALID_TOKEN", "message": "Token inválido"}})

    if not payload.get("activo", False):
        raise HTTPException(status_code=403, detail={"error": {"code": "USER_INACTIVE", "message": "Usuario inactivo, acceso denegado"}})

    return payload

# valida que el usuario sea administrador

def verificar_admin(user_data: dict = Depends(verificar_token)):
    if user_data.get("rol") != "administrador":
        raise HTTPException(
            status_code=403,
            detail={"error": {"code": "ACCESS_DENIED", "message": "Acceso denegado. Se requiere rol de administrador."}}
        )
    return user_data