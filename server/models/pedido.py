from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class PedidoBase(BaseModel):
    tienda: str = Field(..., description="Tienda del pedido (Saga o Ripley)")
    fecha: date = Field(..., description="Fecha del pedido")
    nodo_destino: int = Field(..., description="Nodo de destino (donde se entrega el pedido)")
    # Información del cliente
    cliente_nombre: str = Field(..., description="Nombre del cliente")
    cliente_direccion: str = Field(..., description="Dirección del cliente")
    cliente_telefono: Optional[str] = Field(None, description="Teléfono del cliente")

class PedidoCreate(PedidoBase):
    pass

class PedidoUpdate(BaseModel):
    tienda: Optional[str] = None
    fecha: Optional[date] = None
    nodo_destino: Optional[int] = None
    cliente_nombre: Optional[str] = None
    cliente_direccion: Optional[str] = None
    cliente_telefono: Optional[str] = None

class Pedido(PedidoBase):
    id: int
    ruta_optimizada: Optional[List[int]] = Field(None, description="Ruta optimizada calculada por TSP")
    
    class Config:
        from_attributes = True

