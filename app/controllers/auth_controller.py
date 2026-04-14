import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from app.models.models import UserLogin

# CONFIGURACIÓN (Usa la misma que en el middleware)
SECRET_KEY = "tu_clave_secreta_aqui"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Base de datos de usuarios precargados en memoria
USUARIOS_DB = {
    "admin": {
        "id": 1,
        "password": "admin123",
        "activo": True,
        "rol": "administrador",
        "email": "admin@tienda.com"
    },
    "estudiante": {
        "id": 2,
        "password": "est2025",
        "activo": True,
        "rol": "usuario",
        "email": "estudiante@tienda.com"
    },
    "inactivo": {
        "id": 3,
        "password": "noactivo1",
        "activo": False,
        "rol": "usuario",
        "email": "inactivo@tienda.com"
    }
}

# crea token jwt con expiracion

def crear_token(data: dict):
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# valida usuario y genera el token

def login_user(datos: UserLogin):
    user = USUARIOS_DB.get(datos.usuario)
    
    if not user or user["password"] != datos.password:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Usuario o contraseña incorrectos"}}
        )
    
    token_data = {
        "sub": str(user["id"]),
        "usuario": datos.usuario,
        "activo": user["activo"],
        "rol": user["rol"]
    }
    
    token = crear_token(token_data)
    
    return {
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    }