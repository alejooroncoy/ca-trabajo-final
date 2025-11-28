from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Tuple
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.ruta_service import RutaService
from repository.pedido_repository import PedidoRepository

router = APIRouter()
ruta_service = RutaService()
pedido_repository = PedidoRepository()

class CalcularRutaRequest(BaseModel):
    pedido_id: int
    
    class Config:
        from_attributes = True

class CalcularRutaMultipleRequest(BaseModel):
    pedido_ids: List[int]
    nodo_origen: int  # Nodo de origen (Saga o Ripley)
    
    class Config:
        from_attributes = True

class RutaResponse(BaseModel):
    pedido_id: int
    ruta: List[int]
    distancia_total: float
    coordenadas: List[List[float]]  # Coordenadas de los nodos principales (para compatibilidad)
    segmentos: List[List[List[float]]] = []  # Segmentos del camino real en el grafo

@router.post("/calcular", response_model=RutaResponse)
def calcular_ruta(request: CalcularRutaRequest):
    """Calcula la ruta optimizada para un pedido (punto A a punto B)"""
    pedido = pedido_repository.get_by_id(request.pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    if not pedido.nodos or len(pedido.nodos) < 2:
        raise HTTPException(status_code=400, detail="El pedido debe tener al menos 2 nodos (origen y destino)")
    
    # Usar solo los primeros 2 nodos como origen y destino
    origen = pedido.nodos[0]
    destino = pedido.nodos[1]
    ruta_optimizada = [origen, destino]
    
    print(f"Calculando ruta de punto A a punto B: {origen} -> {destino}")
    
    # Calcular camino mínimo entre origen y destino
    from services.ruta_service import convertir_utm_a_latlon
    ruta_camino, distancia_total, coords_segmento = ruta_service.calcular_ruta_entre_nodos(origen, destino)
    
    # Si se encontró un camino con nodos intermedios, usar esa ruta completa
    if ruta_camino and len(ruta_camino) > 2:
        ruta_optimizada = ruta_camino
        print(f"Ruta encontrada con {len(ruta_camino)} nodos intermedios")
    
    # Construir segmentos (solo uno entre origen y destino)
    segmentos = []
    if coords_segmento and len(coords_segmento) > 0:
        segmentos.append(coords_segmento)
        print(f"Segmento calculado con {len(coords_segmento)} puntos")
    else:
        # Fallback: línea recta si no hay camino en el grafo
        coords_origen_utm = ruta_service.grafo.graph.get_node_coords(origen)
        coords_destino_utm = ruta_service.grafo.graph.get_node_coords(destino)
        
        if coords_origen_utm and coords_origen_utm != (0, 0) and coords_destino_utm and coords_destino_utm != (0, 0):
            lat_origen, lon_origen = convertir_utm_a_latlon(coords_origen_utm[0], coords_origen_utm[1])
            lat_destino, lon_destino = convertir_utm_a_latlon(coords_destino_utm[0], coords_destino_utm[1])
            segmentos.append([(lat_origen, lon_origen), (lat_destino, lon_destino)])
            print("Usando línea recta como fallback")
    
    # Obtener coordenadas de TODOS los nodos de la ruta (incluyendo intermedios)
    coordenadas = []
    if coords_segmento and len(coords_segmento) > 0:
        # Usar las coordenadas del segmento que ya incluyen todos los nodos intermedios
        coordenadas = [[lat, lon] for lat, lon in coords_segmento]
        print(f"Coordenadas obtenidas del segmento: {len(coordenadas)} puntos")
    else:
        # Fallback: obtener coordenadas de todos los nodos de la ruta optimizada
        for nodo_id in ruta_optimizada:
            coords_utm = ruta_service.grafo.graph.get_node_coords(nodo_id)
            if coords_utm and coords_utm != (0, 0):
                lat, lon = convertir_utm_a_latlon(coords_utm[0], coords_utm[1])
                coordenadas.append([lat, lon])
        print(f"Coordenadas obtenidas de ruta optimizada: {len(coordenadas)} puntos")
    
    # Actualizar el pedido con la ruta optimizada
    pedido_repository.update_ruta_optimizada(request.pedido_id, ruta_optimizada)
    
    return RutaResponse(
        pedido_id=request.pedido_id,
        ruta=ruta_optimizada,
        distancia_total=distancia_total,
        coordenadas=coordenadas,
        segmentos=[[[lat, lon] for lat, lon in segmento] for segmento in segmentos]
    )

@router.get("/pedido/{pedido_id}", response_model=RutaResponse)
def obtener_ruta_pedido(pedido_id: int):
    """Obtiene la ruta de un pedido (calcula si no existe) - punto A a punto B"""
    pedido = pedido_repository.get_by_id(pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    if not pedido.nodos or len(pedido.nodos) < 2:
        raise HTTPException(status_code=400, detail="El pedido debe tener al menos 2 nodos (origen y destino)")
    
    # Usar solo los primeros 2 nodos como origen y destino
    origen = pedido.nodos[0]
    destino = pedido.nodos[1]
    
    # Si ya tiene ruta optimizada, usarla; si no, calcularla
    if pedido.ruta_optimizada and len(pedido.ruta_optimizada) >= 2:
        ruta_optimizada = pedido.ruta_optimizada
        origen = ruta_optimizada[0]
        destino = ruta_optimizada[-1]
    else:
        ruta_optimizada = [origen, destino]
    
    # Calcular camino mínimo entre origen y destino
    from services.ruta_service import convertir_utm_a_latlon
    ruta_camino, distancia_total, coords_segmento = ruta_service.calcular_ruta_entre_nodos(origen, destino)
    
    # Si se encontró un camino con nodos intermedios, usar esa ruta completa
    if ruta_camino and len(ruta_camino) > 2:
        ruta_optimizada = ruta_camino
    
    # Construir segmentos (solo uno entre origen y destino)
    segmentos = []
    if coords_segmento and len(coords_segmento) > 0:
        segmentos.append(coords_segmento)
    else:
        # Fallback: línea recta si no hay camino en el grafo
        coords_origen_utm = ruta_service.grafo.graph.get_node_coords(origen)
        coords_destino_utm = ruta_service.grafo.graph.get_node_coords(destino)
        
        if coords_origen_utm and coords_origen_utm != (0, 0) and coords_destino_utm and coords_destino_utm != (0, 0):
            lat_origen, lon_origen = convertir_utm_a_latlon(coords_origen_utm[0], coords_origen_utm[1])
            lat_destino, lon_destino = convertir_utm_a_latlon(coords_destino_utm[0], coords_destino_utm[1])
            segmentos.append([(lat_origen, lon_origen), (lat_destino, lon_destino)])
    
    # Obtener coordenadas de TODOS los nodos de la ruta (incluyendo intermedios)
    coordenadas = []
    if coords_segmento and len(coords_segmento) > 0:
        # Usar las coordenadas del segmento que ya incluyen todos los nodos intermedios
        coordenadas = [[lat, lon] for lat, lon in coords_segmento]
    else:
        # Fallback: obtener coordenadas de todos los nodos de la ruta optimizada
        for nodo_id in ruta_optimizada:
            coords_utm = ruta_service.grafo.graph.get_node_coords(nodo_id)
            if coords_utm and coords_utm != (0, 0):
                lat, lon = convertir_utm_a_latlon(coords_utm[0], coords_utm[1])
                coordenadas.append([lat, lon])
    
    # Actualizar el pedido con la ruta optimizada si no tenía una
    if not pedido.ruta_optimizada:
        pedido_repository.update_ruta_optimizada(pedido_id, ruta_optimizada)
    
    return RutaResponse(
        pedido_id=pedido_id,
        ruta=ruta_optimizada,
        distancia_total=distancia_total,
        coordenadas=coordenadas,
        segmentos=[[[lat, lon] for lat, lon in segmento] for segmento in segmentos]
    )

@router.post("/calcular-multiple", response_model=RutaResponse)
def calcular_ruta_multiple(request: CalcularRutaMultipleRequest):
    """
    Calcula la ruta optimizada para múltiples pedidos.
    La ruta comienza en el origen, visita todos los destinos seleccionados (TSP),
    y regresa al origen.
    """
    if not request.pedido_ids or len(request.pedido_ids) == 0:
        raise HTTPException(status_code=400, detail="Debe seleccionar al menos un pedido")
    
    # Obtener todos los pedidos
    pedidos = []
    nodos_destino = []
    for pedido_id in request.pedido_ids:
        pedido = pedido_repository.get_by_id(pedido_id)
        if not pedido:
            raise HTTPException(status_code=404, detail=f"Pedido {pedido_id} no encontrado")
        pedidos.append(pedido)
        nodos_destino.append(pedido.nodo_destino)
    
    print(f"Calculando ruta múltiple desde nodo {request.nodo_origen} para {len(nodos_destino)} destinos")
    
    # Construir lista completa: origen + destinos + origen (retorno)
    nodos_completos = [request.nodo_origen] + nodos_destino + [request.nodo_origen]
    
    # Calcular ruta optimizada usando TSP (incluye retorno al origen)
    ruta_optimizada, distancia_total, segmentos = ruta_service.calcular_ruta_completa_con_segmentos(nodos_completos)
    
    # Si TSP no devolvió la ruta completa, construirla manualmente
    if not ruta_optimizada or len(ruta_optimizada) == 0:
        # Fallback: usar orden directo
        ruta_optimizada = nodos_completos
        distancia_total = 0.0
        segmentos = []
    
    # Asegurar que la ruta comienza y termina en el origen
    if ruta_optimizada[0] != request.nodo_origen:
        ruta_optimizada.insert(0, request.nodo_origen)
    if ruta_optimizada[-1] != request.nodo_origen:
        ruta_optimizada.append(request.nodo_origen)
    
    # Obtener coordenadas de todos los nodos de la ruta
    from services.ruta_service import convertir_utm_a_latlon
    coordenadas = []
    if segmentos and len(segmentos) > 0:
        # Usar coordenadas de los segmentos
        for segmento in segmentos:
            coordenadas.extend([[lat, lon] for lat, lon in segmento])
    else:
        # Fallback: obtener coordenadas de cada nodo
        for nodo_id in ruta_optimizada:
            coords_utm = ruta_service.grafo.graph.get_node_coords(nodo_id)
            if coords_utm and coords_utm != (0, 0):
                lat, lon = convertir_utm_a_latlon(coords_utm[0], coords_utm[1])
                coordenadas.append([lat, lon])
    
    print(f"Ruta múltiple calculada: {len(ruta_optimizada)} nodos, distancia total: {distancia_total:.2f} km")
    
    return RutaResponse(
        pedido_id=request.pedido_ids[0] if request.pedido_ids else 0,  # Usar primer pedido como referencia
        ruta=ruta_optimizada,
        distancia_total=distancia_total,
        coordenadas=coordenadas,
        segmentos=[[[lat, lon] for lat, lon in segmento] for segmento in segmentos] if segmentos else []
    )

