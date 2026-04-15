from fastapi import FastAPI, Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
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
    title="API de Productos",
    version="1.0.0",
    openapi_tags=tags_metadata
)

# maneja errores de validacion de entrada
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = []
    for err in exc.errors():
        loc = err.get("loc", [])
        field = ".".join(str(x) for x in loc[1:]) if len(loc) > 1 else ".".join(str(x) for x in loc)
        details.append({"field": field, "message": err.get("msg")})
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Datos de entrada inválidos",
                "details": details
            }
        }
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
# sirve el index html de la app
async def read_index():
    ruta_html = os.path.join(os.path.dirname(__file__), "index.html")
    with open(ruta_html, "r", encoding="utf-8") as f:
        return f.read()

# --- SECCIÓN 2: AUTH ---
@app.post("/auth", tags=["Auth"], summary="Login")
# login y retorna token jwt
def login(datos: UserLogin):
    return ac.login_user(datos)

# --- SECCIÓN 3: PRODUCTOS ---

@app.get("/productos", tags=["Productos"], summary="Listar productos con filtros opcionales")
# lista productos con filtros en query params
def listar(
    nombre: str = None, 
    subcategoria: str = None, 
    precio_min: float = None, 
    precio_max: float = None, 
    estado: str = None, 
    page: int = 1, 
    limit: int = 10,
    user=Depends(verificar_token)
):
    return pc.listar_productos(
        nombre=nombre, 
        subcategoria=subcategoria, 
        precio_min=precio_min, 
        precio_max=precio_max, 
        estado=estado, 
        page=page, 
        limit=limit
    )

@app.get("/productos/{producto_id}", tags=["Productos"], summary="Obtener producto por id")
# obtiene un producto especifico por id
def obtener_producto(producto_id: int, user=Depends(verificar_token)):
    return pc.obtener_producto_id(producto_id)

@app.post("/productos", tags=["Productos"], summary="Crear", status_code=201)
# crea un producto nuevo
def crear(item: Producto, user=Depends(verificar_admin)):
    return pc.crear_nuevo_producto(item)

@app.put("/productos/{producto_id}", tags=["Productos"], summary="Actualizar")
# actualiza un producto completo por id
def actualizar(producto_id: int, item: Producto, user=Depends(verificar_admin)):
    return pc.actualizar_producto_id(producto_id, item)

@app.delete("/productos/{producto_id}", tags=["Productos"])
# elimina un producto por id
def eliminar(producto_id: int, user=Depends(verificar_admin)): # <--- IMPORTANTE: verificar_admin
    return pc.eliminar_producto_id(producto_id)