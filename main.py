from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from app.models.models import Producto, UserLogin
from app.controllers import producto_controller as pc
from app.controllers import auth_controller as ac
from app.controllers.middleware import verificar_token, verificar_admin
import os

# 1. Configuración de etiquetas para el orden en Swagger (/docs)
tags_metadata = [
    {
        "name": "Frontend",
        "description": "Rutas para servir la interfaz gráfica.",
    },
    {
        "name": "Auth",
        "description": "Autenticación y tokens JWT.",
    },
    {
        "name": "Productos",
        "description": "Gestión completa del inventario (CRUD).",
    },
]

app = FastAPI(
    title="SamantaWeb API",
    version="1.0.0",
    openapi_tags=tags_metadata
)

# 2. Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SECCIÓN 1: FRONTEND ---
@app.get("/", tags=["Frontend"], summary="Index", response_class=HTMLResponse)
async def read_index():
    # Buscamos el index.html dentro de app/views/
    ruta_html = os.path.join(os.path.dirname(__file__), "app", "views", "index.html")
    with open(ruta_html, "r", encoding="utf-8") as f:
        return f.read()

# --- SECCIÓN 2: AUTH ---
@app.post("/auth", tags=["Auth"], summary="Login")
def login(datos: UserLogin):
    return ac.login_user(datos)

# --- SECCIÓN 3: PRODUCTOS ---

@app.get("/productos", tags=["Productos"], summary="Listar")
def listar(user=Depends(verificar_token)):
    return pc.listar_productos()

@app.post("/productos", tags=["Productos"], summary="Crear", status_code=201)
def crear(item: Producto, user=Depends(verificar_admin)):
    return pc.crear_nuevo_producto(item)

@app.put("/productos/{producto_id}", tags=["Productos"], summary="Actualizar")
def actualizar(producto_id: int, item: Producto, user=Depends(verificar_admin)):
    return pc.actualizar_producto_id(producto_id, item)

@app.patch("/productos/{producto_id}/stock", tags=["Productos"], summary="Actualizar Stock")
def stock(producto_id: int, nuevo_stock: int, user=Depends(verificar_token)):
    return pc.actualizar_solo_stock(producto_id, nuevo_stock)

@app.delete("/productos/{producto_id}", tags=["Productos"], summary="Eliminar")
def eliminar(producto_id: int, user=Depends(verificar_admin)):
    return pc.eliminar_producto_id(producto_id)