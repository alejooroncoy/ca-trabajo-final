from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class PedidoBase(BaseModel):
    tienda: str = Field(..., description="Tienda del pedido (Saga o Ripley)")
    fecha: date = Field(..., description="Fecha del pedido")
    nodos: List[int] = Field(..., description="Lista de nodos a visitar")

class PedidoCreate(PedidoBase):
    pass

class PedidoUpdate(BaseModel):
    tienda: Optional[str] = None
    fecha: Optional[date] = None
    nodos: Optional[List[int]] = None

class Pedido(PedidoBase):
    id: int
    ruta_optimizada: Optional[List[int]] = Field(None, description="Ruta optimizada calculada por TSP")
    
    class Config:
        from_attributes = True

