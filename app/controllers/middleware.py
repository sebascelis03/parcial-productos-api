import jwt
import datetime
from fastapi import Header, HTTPException, Depends

# Esta clave debe ser la misma que usaste en el login
SECRET_KEY = "tu_clave_secreta_aqui" 

def verificar_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail={"error": {"message": "No se envió el encabezado"}})
    
    try:
        # Extraemos el token del formato "Bearer <token>"
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload 
    except Exception as e:
        raise HTTPException(status_code=401, detail={"error": {"message": "Token inválido o expirado"}})

def verificar_admin(user_data: dict = Depends(verificar_token)):
    if user_data.get("rol") != "administrador":
        raise HTTPException(status_code=403, detail={"error": {"message": "Acceso restringido a administradores"}})
    return user_data