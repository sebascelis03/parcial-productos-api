from typing import Literal
from pydantic import BaseModel, Field

class Producto(BaseModel):
    nombre: str
    descripcion: str
    subcategoria: str
    precio: float = Field(gt=0)
    precioxcantidad: float = Field(gt=0)
    estado: Literal["activo", "inactivo"]
    stock: int = Field(ge=0)

class UserLogin(BaseModel):
    usuario: str
    password: str