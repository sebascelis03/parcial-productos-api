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

# 3. Listar todos los productos (GET)
@app.get("/productos")
def obtener_productos():
    return {"data": productos_db}

# 4. Obtener un producto por ID (GET)
@app.get("/productos/{producto_id}")
def obtener_producto(producto_id: int):
    # Buscamos el producto en la lista
    for p in productos_db:
        if p["id"] == producto_id:
            return {"data": p}
    # Si no existe, error 404 como pide el examen
    raise HTTPException(status_code=404, detail=f"No se encontró el producto con id {producto_id}")

# 5. Crear un producto (POST)
@app.post("/productos", status_code=201)
def crear_producto(item: Producto):
    global contador_id
    # Convertimos el modelo a diccionario y le asignamos ID
    nuevo_producto = item.dict()
    nuevo_producto["id"] = contador_id
    
    productos_db.append(nuevo_producto)
    contador_id += 1 # Aumentamos para el siguiente producto
    
    return {"data": nuevo_producto}

# 6. Actualizar un producto (PUT)
@app.put("/productos/{producto_id}")
def actualizar_producto(producto_id: int, item_actualizado: Producto):
    for i, p in enumerate(productos_db):
        if p["id"] == producto_id:
            # Creamos el diccionario con los nuevos datos pero mantenemos el mismo ID
            producto_editado = item_actualizado.dict()
            producto_editado["id"] = producto_id
            
            # Reemplazamos en la lista
            productos_db[i] = producto_editado
            return {"data": producto_editado}
    
    # Si llegamos aquí es porque no se encontró
    raise HTTPException(status_code=404, detail=f"No se encontró el producto con id {producto_id}")

# 7. Eliminar un producto (DELETE)
@app.delete("/productos/{producto_id}")
def eliminar_producto(producto_id: int):
    for i, p in enumerate(productos_db):
        if p["id"] == producto_id:
            productos_db.pop(i) # Lo sacamos de la lista
            return {"data": {"message": "Producto eliminado exitosamente"}}
            
    raise HTTPException(status_code=404, detail=f"No se encontró el producto con id {producto_id}")