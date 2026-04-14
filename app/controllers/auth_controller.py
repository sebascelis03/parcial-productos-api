import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from app.models.models import UserLogin

# CONFIGURACIÓN (Usa la misma que en el middleware)
SECRET_KEY = "tu_clave_secreta_aqui" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Base de datos de usuarios (puedes mover esto a un JSON luego)
USUARIOS_DB = {
    "admin": {"password": "admin123", "rol": "administrador", "email": "admin@samanta.com"},
    "empleado": {"password": "emp123", "rol": "empleado", "email": "staff@samanta.com"}
}

def crear_token(data: dict):
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    # IMPORTANTE: El 'sub' debe ser un string para evitar el error que te salía en consola
    payload.update({"sub": str(data.get("usuario"))}) 
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def login_user(datos: UserLogin):
    user = USUARIOS_DB.get(datos.usuario)
    
    # 1. Validar si el usuario existe y la contraseña coincide
    if not user or user["password"] != datos.password:
        raise HTTPException(
            status_code=401, 
            detail={"error": {"message": "Usuario o contraseña incorrectos"}}
        )
    
    # 2. Preparar los datos que irán dentro del token
    token_data = {
        "usuario": datos.usuario,
        "rol": user["rol"],
        "email": user["email"]
    }
    
    token = crear_token(token_data)
    
    # 3. Devolver la respuesta al frontend
    return {
        "data": {
            "access_token": token,
            "token_type": "bearer"
        }
    }