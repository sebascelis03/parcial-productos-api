from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import jwt
import datetime
import json
import os

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de Archivos y Seguridad
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_JSON = os.path.join(BASE_DIR, "productos.json")
SECRET_KEY = "mi_clave_secreta_pro"

# --- FUNCIONES DE PERSISTENCIA ---
def cargar_datos():
    if not os.path.exists(ARCHIVO_JSON):
        with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []
    try:
        with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
            contenido = f.read().strip()
            return json.loads(contenido) if contenido else []
    except:
        return []

def guardar_datos(datos):
    try:
        with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error al guardar: {e}")
        return False

# --- BASE DE DATOS DE USUARIOS ---
usuarios_db = [
    { "id": 1, "usuario": "admin", "email": "admin@tienda.com", "rol": "administrador", "password": "admin123", "activo": True },
    { "id": 2, "usuario": "empleado", "email": "empleado@tienda.com", "rol": "empleado", "password": "emp123", "activo": True },
    { "id": 3, "usuario": "inactivo", "email": "inactivo@tienda.com", "rol": "invitado", "password": "noactivo1", "activo": False }
]

# --- MODELOS ---
class Producto(BaseModel):
    nombre: str
    descripcion: str
    subcategoria: str
    precio: float = Field(gt=0)
    precioxcantidad: float = Field(gt=0)
    estado: str
    stock: int = Field(ge=0)

# --- SEGURIDAD (JWT) ---
def verificar_token(authorization: str = Header(None)):
    # Imprime para debug (verás esto en la terminal negra)
    print(f"DEBUG: Header recibido: {authorization}") 

    if not authorization:
        raise HTTPException(status_code=401, detail={"error": {"message": "No se envió el encabezado de autorización"}})
    
    try:
        # Esto maneja si el navegador envía "Bearer token" o "bearer token"
        scheme, _, token = authorization.partition(' ')
        if scheme.lower() != 'bearer' or not token:
            raise Exception("Formato de token inválido. Se espera 'Bearer <token>'")
             
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload 
    except Exception as e:
        print(f"DEBUG Error JWT: {str(e)}")
        raise HTTPException(status_code=401, detail={"error": {"message": f"Token no válido o expirado: {str(e)}"}})

def verificar_admin(user_data: dict = Depends(verificar_token)):
    if user_data.get("rol") != "administrador":
        raise HTTPException(status_code=403, detail={"error": {"message": "Se requieren permisos de administrador"}})
    return user_data

# --- ENDPOINTS ---

@app.post("/auth")
def login(datos: dict):
    usuario = datos.get("usuario")
    password = datos.get("password")
    user = next((u for u in usuarios_db if u["usuario"] == usuario and u["password"] == password), None)
    
    if not user:
        raise HTTPException(status_code=401, detail={"error": {"message": "Credenciales inválidas"}})
    
    payload = {
        "sub": str(user["id"]),
        "usuario": user["usuario"],
        "email": user["email"],
        "rol": user["rol"],
        "activo": user["activo"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return {"data": {"access_token": token, "token_type": "Bearer"}}

@app.get("/productos")
def obtener_productos(user_data: dict = Depends(verificar_token)):
    return {"data": cargar_datos()}

@app.post("/productos", status_code=201)
def crear_producto(item: Producto, user_data: dict = Depends(verificar_admin)):
    productos = cargar_datos()
    nuevo_p = item.dict()
    nuevo_p["id"] = max([p["id"] for p in productos], default=0) + 1
    productos.append(nuevo_p)
    if guardar_datos(productos):
        return {"data": nuevo_p}
    raise HTTPException(status_code=500, detail={"error": {"message": "Error al guardar en JSON"}})

@app.put("/productos/{producto_id}")
def actualizar_producto(producto_id: int, item_actualizado: Producto, user_data: dict = Depends(verificar_admin)):
    productos = cargar_datos()
    
    # Buscamos la posición del producto
    indice = next((i for i, p in enumerate(productos) if p["id"] == producto_id), None)
    
    if indice is None:
        raise HTTPException(
            status_code=404, 
            detail={"error": {"message": f"No se encontró el producto con ID {producto_id}"}}
        )
    
    # Mantenemos el mismo ID, pero actualizamos el resto
    producto_editado = item_actualizado.dict()
    producto_editado["id"] = producto_id
    
    productos[indice] = producto_editado
    
    if guardar_datos(productos):
        return {"data": producto_editado}
    else:
        raise HTTPException(status_code=500, detail={"error": {"message": "Error al escribir en el JSON"}})

@app.delete("/productos/{producto_id}")
def eliminar_producto(producto_id: int, user_data: dict = Depends(verificar_admin)):
    productos = cargar_datos()
    nuevos_productos = [p for p in productos if p["id"] != producto_id]
    if len(nuevos_productos) == len(productos):
        raise HTTPException(status_code=404, detail={"error": {"message": "No encontrado"}})
    guardar_datos(nuevos_productos)
    return {"data": {"message": "Eliminado"}}


@app.patch("/productos/{producto_id}/stock")
def actualizar_stock(producto_id: int, nuevo_stock: int, user_data: dict = Depends(verificar_token)):
    # Buscamos al usuario por su rol en el token
    # Si es admin o empleado, lo dejamos pasar
    if user_data.get("rol") not in ["administrador", "empleado"]:
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar inventario")
    
    productos = cargar_datos()
    for p in productos:
        if p["id"] == producto_id:
            p["stock"] = nuevo_stock
            guardar_datos(productos)
            return {"data": p}
            
    raise HTTPException(status_code=404, detail="Producto no encontrado")