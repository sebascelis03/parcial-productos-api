import json
import os
from fastapi import HTTPException, Depends
from app.models.models import Producto

# Ruta al JSON (puedes definirla aquí o traerla de config)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARCHIVO_JSON = os.path.join(BASE_DIR, "productos.json")

# lee productos desde el archivo json

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

# escribe productos en el archivo json

def guardar_datos(datos):
    try:
        with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error al guardar: {e}")
        return False

# --- FUNCIONES DE LÓGICA (CONTROLADOR) ---

# agrega un producto nuevo con id autogenerado

def crear_nuevo_producto(item: Producto):
    productos = cargar_datos()
    nuevo_p = item.dict()
    nuevo_p["id"] = max([p["id"] for p in productos], default=0) + 1
    productos.append(nuevo_p)
    if guardar_datos(productos):
        return {"data": nuevo_p}
    raise HTTPException(status_code=500, detail={"error": {"message": "Error al guardar en JSON"}})

# actualiza un producto por su id

def actualizar_producto_id(producto_id: int, item_actualizado: Producto):
    productos = cargar_datos()
    indice = next((i for i, p in enumerate(productos) if p["id"] == producto_id), None)
    
    if indice is None:
        raise HTTPException(status_code=404, detail={"error": {"code": "PRODUCT_NOT_FOUND", "message": "Producto no encontrado"}})
    
    producto_editado = item_actualizado.dict()
    producto_editado["id"] = producto_id
    productos[indice] = producto_editado
    
    if guardar_datos(productos):
        return {"data": producto_editado}
    raise HTTPException(status_code=500, detail={"error": {"code": "INTERNAL_ERROR", "message": "Error al escribir en JSON"}})

# obtiene un producto por su id

def obtener_producto_id(producto_id: int):
    productos = cargar_datos()
    producto = next((p for p in productos if p["id"] == producto_id), None)
    if not producto:
        raise HTTPException(status_code=404, detail={"error": {"code": "PRODUCT_NOT_FOUND", "message": f"Producto con id {producto_id} no encontrado"}})
    return {"data": producto}

# --- LO QUE TE FALTABA ---

# elimina un producto por id

def eliminar_producto_id(producto_id: int):
    productos = cargar_datos()
    # Filtramos para quitar el que tiene ese ID
    productos_nuevos = [p for p in productos if p["id"] != producto_id]
    
    if len(productos_nuevos) == len(productos):
        raise HTTPException(status_code=404, detail={"error": {"code": "PRODUCT_NOT_FOUND", "message": "Producto no existe"}})
    
    if guardar_datos(productos_nuevos):
        return {"data": {"message": "Producto eliminado con éxito"}}
    raise HTTPException(status_code=500, detail={"error": {"code": "INTERNAL_ERROR", "message": "Error al borrar en JSON"}})

# actualiza solo el stock de un producto por id

def actualizar_solo_stock(producto_id: int, nuevo_stock: int):
    productos = cargar_datos()
    for p in productos:
        if p["id"] == producto_id:
            p["stock"] = nuevo_stock
            if guardar_datos(productos):
                return {"data": p}
            raise HTTPException(status_code=500, detail={"error": {"code": "INTERNAL_ERROR", "message": "Error al guardar stock"}})
    
    raise HTTPException(status_code=404, detail={"error": {"code": "PRODUCT_NOT_FOUND", "message": "Producto no encontrado"}})

# lista productos con filtros y paginacion

def listar_productos(nombre: str = None, subcategoria: str = None, precio_min: float = None, precio_max: float = None, estado: str = None, page: int = 1, limit: int = 10):
    productos = cargar_datos() # Carga tu JSON
    
    # FILTROS (Case insensitive donde aplique)
    if nombre:
        productos = [p for p in productos if nombre.lower() in p["nombre"].lower()]
    
    if subcategoria:
        productos = [p for p in productos if subcategoria.lower() in p["subcategoria"].lower()]
    
    if precio_min is not None:
        productos = [p for p in productos if p["precio"] >= precio_min]
    
    if precio_max is not None:
        productos = [p for p in productos if p["precio"] <= precio_max]
    
    if estado:
        productos = [p for p in productos if estado.lower() in p["estado"].lower()]
    
    # PAGINACIÓN (Obligatorio Nivel 3)
    start = (page - 1) * limit
    end = start + limit
    productos_paginados = productos[start:end]
    
    # RESPUESTA NIVEL 3 (Siempre dentro de "data")
    return {
        "data": productos_paginados,
        "pagination": {
            "total": len(productos),
            "page": page,
            "limit": limit,
            "totalPages": (len(productos) + limit - 1) // limit
        }
    }