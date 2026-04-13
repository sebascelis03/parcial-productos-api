from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
import jwt
import datetime

app = FastAPI()

# 1. Datos precargados (Usuarios)
usuarios_db = [
    { "id": 1, "usuario": "admin", "password": "admin123", "activo": True },
    { "id": 2, "usuario": "estudiante", "password": "est2025", "activo": True },
    { "id": 3, "usuario": "inactivo", "password": "noactivo1", "activo": False }
]

# 2. Almacenamiento en memoria para productos
productos_db = []
contador_id = 1

# Modelo de datos para Producto (Lo que recibimos)
class Producto(BaseModel):
    nombre: str
    descripcion: str
    subcategoria: str
    precio: float
    precioxcantidad: float
    estado: str

@app.get("/")
def inicio():
    return {"mensaje": "API de Productos funcionando"}

SECRET_KEY = "mi_clave_secreta_pro" # Esta es tu firma personal

@app.post("/auth")
def login(datos: dict):
    usuario = datos.get("usuario")
    password = datos.get("password")
    
    # Buscamos si el usuario existe en nuestra lista de memoria
    user_found = next((u for u in usuarios_db if u["usuario"] == usuario and u["password"] == password), None)
    
    if not user_found:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    
    # Creamos la "llave" (JWT) que vence en 1 hora
    payload = {
        "sub": user_found["id"],
        "usuario": user_found["usuario"],
        "activo": user_found["activo"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    return {
        "data": {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": 3600
        }
    }

# Endpoint de salud (opcional pero recomendado por tu profe)
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Servidor funcionando"}