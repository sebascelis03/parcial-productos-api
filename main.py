from fastapi import FastAPI, HTTPException, Depends, status, Header, Request
from pydantic import BaseModel, Field
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
    precio: float = Field(gt=0) # gt=0 significa "Greater Than 0"
    precioxcantidad: float = Field(gt=0)
    estado: str # Validaremos que sea 'activo' o 'inactivo' en la lógica

@app.get("/")
def inicio():
    return {"mensaje": "API de Productos funcionando"}

SECRET_KEY = "mi_clave_secreta_pro" # Esta es tu firma personal

# Función para verificar el token y si el usuario está activo (Nivel 2)
def verificar_token(authorization: str = Header(None)):
    if authorization is None:
        raise HTTPException(
            status_code=401, 
            detail={"error": {"code": "NO_TOKEN", "message": "Token de autenticación requerido"}}
        )
    
    try:
        # El formato suele ser "Bearer <token>", así que lo separamos
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        # Validación de usuario activo (Punto 5 del examen)
        if not payload.get("activo"):
            raise HTTPException(
                status_code=403, 
                detail={"error": {"code": "USER_INACTIVE", "message": "Usuario inactivo, acceso denegado"}}
            )
            
        return payload # Si todo está bien, devuelve los datos del usuario
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail={"error": {"code": "TOKEN_EXPIRED", "message": "El token ha expirado"}})
    except Exception:
        raise HTTPException(status_code=401, detail={"error": {"code": "INVALID_TOKEN", "message": "Token inválido"}})

@app.post("/auth")
def login(datos: dict):
    usuario = datos.get("usuario")
    password = datos.get("password")
    
    user_found = next((u for u in usuarios_db if u["usuario"] == usuario and u["password"] == password), None)
    
    if not user_found:
        # Error con estructura Nivel 2 (punto 6 del examen)
        raise HTTPException(
            status_code=401, 
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Usuario o contraseña incorrectos"}}
        )
    
    payload = {
        "sub": user_found["id"],
        "usuario": user_found["usuario"],
        "activo": user_found["activo"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    # Respuesta con estructura Nivel 2 (punto 6 del examen)
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
def obtener_productos(
    page: int = 1, 
    limit: int = 5, 
    subcategoria: Optional[str] = None,
    estado: Optional[str] = None,
    nombre: Optional[str] = None,
    user_data: dict = Depends(verificar_token)
):
    # Aplicar filtros (Nivel 3)
    resultados = productos_db
    if subcategoria:
        resultados = [p for p in resultados if p["subcategoria"].lower() == subcategoria.lower()]
    if estado:
        resultados = [p for p in resultados if p["estado"].lower() == estado.lower()]
    if nombre:
        resultados = [p for p in resultados if nombre.lower() in p["nombre"].lower()]

    # Paginación (Nivel 3)
    total = len(resultados)
    start = (page - 1) * limit
    end = start + limit
    data_paginada = resultados[start:end]

    return {
        "data": data_paginada,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit
        }
    }

# 4. Obtener un producto por ID (GET)
@app.get("/productos/{producto_id}")
def obtener_producto(producto_id: int, user_data: dict = Depends(verificar_token)):
    # Buscamos el producto en la lista
    for p in productos_db:
        if p["id"] == producto_id:
            return {"data": p}
    # Si no existe, error 404 como pide el examen
    raise HTTPException(
        status_code=404, 
        detail={
            "error": {
                "code": "PRODUCT_NOT_FOUND", 
                "message": f"No se encontró el producto con id {producto_id}"
            }
        }
    )

# 5. Crear un producto (POST)
@app.post("/productos", status_code=201)
def crear_producto(item: Producto, user_data: dict = Depends(verificar_token)):
    global contador_id
    # Convertimos el modelo a diccionario y le asignamos ID
    nuevo_producto = item.dict()
    nuevo_producto["id"] = contador_id
    
    productos_db.append(nuevo_producto)
    contador_id += 1 # Aumentamos para el siguiente producto
    
    return {"data": nuevo_producto}

# 6. Actualizar un producto (PUT)
@app.put("/productos/{producto_id}")
def actualizar_producto(producto_id: int, item_actualizado: Producto, user_data: dict = Depends(verificar_token)):
    for i, p in enumerate(productos_db):
        if p["id"] == producto_id:
            # Creamos el diccionario con los nuevos datos pero mantenemos el mismo ID
            producto_editado = item_actualizado.dict()
            producto_editado["id"] = producto_id
            
            # Reemplazamos en la lista
            productos_db[i] = producto_editado
            return {"data": producto_editado}
    
    # Si llegamos aquí es porque no se encontró el producto, error 404 con estructura Nivel 2
    raise HTTPException(
        status_code=404, 
        detail={
            "error": {
                "code": "PRODUCT_NOT_FOUND", 
                "message": f"No se encontró el producto con id {producto_id}"
            }
        }
    )

# 7. Eliminar un producto (DELETE)
@app.delete("/productos/{producto_id}")
def eliminar_producto(producto_id: int, user_data: dict = Depends(verificar_token)):
    for i, p in enumerate(productos_db):
        if p["id"] == producto_id:
            productos_db.pop(i) # Lo sacamos de la lista
            return {"data": {"message": "Producto eliminado exitosamente"}}
            
    # Si llegamos aquí es porque no se encontró el producto, error 404 con estructura Nivel 2
    raise HTTPException(
        status_code=404, 
        detail={
            "error": {
                "code": "PRODUCT_NOT_FOUND", 
                "message": f"No se encontró el producto con id {producto_id}"
            }
        }
    )