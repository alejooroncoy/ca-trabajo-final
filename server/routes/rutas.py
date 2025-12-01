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
    algoritmo: str = "dijkstra"  # "dijkstra" o "floyd_warshall"
    
    class Config:
        from_attributes = True

class CalcularRutaMultipleRequest(BaseModel):
    pedido_ids: List[int]
    nodo_origen: int  # Nodo de origen (Saga o Ripley)
    algoritmo: str = "dijkstra"  # "dijkstra" o "floyd_warshall"
    
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
    
    print(f"Calculando ruta de punto A a punto B: {origen} -> {destino} usando {request.algoritmo.upper()}")
    
    # Calcular camino mínimo entre origen y destino
    from services.ruta_service import convertir_utm_a_latlon
    ruta_camino, distancia_total, coords_segmento = ruta_service.calcular_ruta_entre_nodos(origen, destino, request.algoritmo)
    
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
    Calcula la ruta optimizada para múltiples pedidos usando OSRM (rutas reales que siguen calles).
    La ruta comienza en el origen, visita todos los destinos seleccionados (TSP),
    y regresa al origen.
    """
    if not request.pedido_ids or len(request.pedido_ids) == 0:
        raise HTTPException(status_code=400, detail="Debe seleccionar al menos un pedido")
    
    # Importar servicios
    from services.ruta_service import convertir_utm_a_latlon
    from services.osrm_service import OSRMService
    
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
    
    # Paso 1: Obtener coordenadas de todos los nodos (origen + destinos)
    def obtener_coordenadas_nodo(nodo_id: int) -> tuple:
        """Obtiene coordenadas (lat, lon) de un nodo"""
        coords_utm = ruta_service.grafo.graph.get_node_coords(nodo_id)
        if coords_utm and coords_utm != (0, 0):
            lat, lon = convertir_utm_a_latlon(coords_utm[0], coords_utm[1])
            return (lat, lon)
        return None
    
    # Obtener coordenadas del origen
    origen_coords = obtener_coordenadas_nodo(request.nodo_origen)
    if not origen_coords:
        raise HTTPException(status_code=400, detail=f"No se pudieron obtener coordenadas del nodo origen {request.nodo_origen}")
    
    # Obtener coordenadas de los destinos
    destinos_coords = []
    for nodo_id in nodos_destino:
        coords = obtener_coordenadas_nodo(nodo_id)
        if coords:
            destinos_coords.append((nodo_id, coords))
        else:
            print(f"Advertencia: No se pudieron obtener coordenadas del nodo {nodo_id}")
    
    if len(destinos_coords) == 0:
        raise HTTPException(status_code=400, detail="No se pudieron obtener coordenadas de los destinos")
    
    # Paso 2: Optimizar orden usando TSP (solo para el orden, no las rutas)
    # Usar TSP del backend para obtener el orden optimizado
    nodos_para_tsp = [nodo_id for nodo_id, _ in destinos_coords]
    nodos_completos_tsp = [request.nodo_origen] + nodos_para_tsp + [request.nodo_origen]
    
    ruta_optimizada_nodos, _, _ = ruta_service.calcular_ruta_completa_con_segmentos(nodos_completos_tsp)
    
    # Si TSP falló, usar orden directo
    if not ruta_optimizada_nodos or len(ruta_optimizada_nodos) < 3:
        ruta_optimizada_nodos = nodos_completos_tsp
    
    # Asegurar que comienza y termina en origen
    if ruta_optimizada_nodos[0] != request.nodo_origen:
        ruta_optimizada_nodos.insert(0, request.nodo_origen)
    if ruta_optimizada_nodos[-1] != request.nodo_origen:
        ruta_optimizada_nodos.append(request.nodo_origen)
    
    # Paso 3: Crear diccionario de coordenadas por nodo_id
    coords_por_nodo = {request.nodo_origen: origen_coords}
    for nodo_id, coords in destinos_coords:
        coords_por_nodo[nodo_id] = coords
    
    # Paso 4: Calcular rutas reales usando OSRM entre cada par consecutivo
    puntos_ordenados = [coords_por_nodo[nodo_id] for nodo_id in ruta_optimizada_nodos if nodo_id in coords_por_nodo]
    
    print(f"Calculando rutas reales con OSRM para {len(puntos_ordenados)} puntos")
    print(f"Puntos ordenados: {puntos_ordenados[:3]}... (mostrando primeros 3)")
    
    # Calcular ruta completa usando OSRM segmento por segmento para mayor precisión
    todas_coordenadas: List[Tuple[float, float]] = []
    distancia_total_km = 0.0
    
    for i in range(len(puntos_ordenados) - 1):
        origen_punto = puntos_ordenados[i]
        destino_punto = puntos_ordenados[i + 1]
        
        print(f"Calculando segmento {i+1}/{len(puntos_ordenados)-1}: {origen_punto} -> {destino_punto}")
        
        resultado_segmento = OSRMService.calcular_ruta_entre_puntos(
            origen_punto,
            destino_punto,
            pasos_intermedios=True
        )
        
        if resultado_segmento:
            coordenadas_segmento, distancia_segmento = resultado_segmento
            print(f"  Segmento calculado: {len(coordenadas_segmento)} puntos, {distancia_segmento:.2f} km")
            
            # Evitar duplicar el último punto
            if todas_coordenadas and coordenadas_segmento:
                if todas_coordenadas[-1] == coordenadas_segmento[0]:
                    todas_coordenadas.extend(coordenadas_segmento[1:])
                else:
                    todas_coordenadas.extend(coordenadas_segmento)
            else:
                todas_coordenadas.extend(coordenadas_segmento)
            
            distancia_total_km += distancia_segmento
        else:
            # Fallback: línea recta
            print(f"  OSRM falló para este segmento, usando línea recta")
            todas_coordenadas.append(origen_punto)
            todas_coordenadas.append(destino_punto)
            distancia_total_km += OSRMService._distancia_haversine(origen_punto, destino_punto)
    
    print(f"Ruta completa: {len(todas_coordenadas)} puntos, {distancia_total_km:.2f} km total")
    
    if todas_coordenadas and len(todas_coordenadas) > 1:
        # Convertir a formato de respuesta
        coordenadas = [[lat, lon] for lat, lon in todas_coordenadas]
        # Crear un segmento único con todas las coordenadas
        segmentos = [coordenadas] if coordenadas else []
        
        return RutaResponse(
            pedido_id=request.pedido_ids[0] if request.pedido_ids else 0,
            ruta=ruta_optimizada_nodos,
            distancia_total=distancia_total_km,
            coordenadas=coordenadas,
            segmentos=segmentos
        )
    else:
        # Fallback: usar línea recta si OSRM falla
        print("OSRM falló, usando línea recta como fallback")
        coordenadas = [[lat, lon] for lat, lon in puntos_ordenados]
        distancia_total = sum(
            OSRMService._distancia_haversine(puntos_ordenados[i], puntos_ordenados[i+1])
            for i in range(len(puntos_ordenados) - 1)
        )
        
        return RutaResponse(
            pedido_id=request.pedido_ids[0] if request.pedido_ids else 0,
            ruta=ruta_optimizada_nodos,
            distancia_total=distancia_total,
            coordenadas=coordenadas,
            segmentos=[[coords] for coords in coordenadas]
        )

