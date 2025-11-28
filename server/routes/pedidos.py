from fastapi import APIRouter, HTTPException
from typing import List, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models.pedido import Pedido, PedidoCreate, PedidoUpdate
from repository.pedido_repository import PedidoRepository

router = APIRouter()
repository = PedidoRepository()

@router.get("/", response_model=List[Pedido])
def listar_pedidos(tienda: Optional[str] = None):
    """Lista todos los pedidos, opcionalmente filtrados por tienda"""
    return repository.get_all(tienda=tienda)

@router.get("/{pedido_id}", response_model=Pedido)
def obtener_pedido(pedido_id: int):
    """Obtiene un pedido por su ID"""
    pedido = repository.get_by_id(pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido

@router.post("/", response_model=Pedido, status_code=201)
def crear_pedido(pedido_data: PedidoCreate):
    """Crea un nuevo pedido"""
    return repository.create(pedido_data)

@router.put("/{pedido_id}", response_model=Pedido)
def actualizar_pedido(pedido_id: int, pedido_data: PedidoUpdate):
    """Actualiza un pedido existente"""
    pedido = repository.update(pedido_id, pedido_data)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido

@router.delete("/{pedido_id}", status_code=204)
def eliminar_pedido(pedido_id: int):
    """Elimina un pedido"""
    if not repository.delete(pedido_id):
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return None

