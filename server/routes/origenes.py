from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models.grafo_wrapper import grafo_wrapper

router = APIRouter()

class OrigenResponse(BaseModel):
    nodo_id: int
    nombre: str
    latitud: float
    longitud: float

def convertir_utm_a_latlon(utm_x: float, utm_y: float):
    """Convierte coordenadas UTM a lat/lon"""
    try:
        from pyproj import Transformer
        transformer = Transformer.from_crs("EPSG:32718", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(utm_x, utm_y)
        return lat, lon
    except ImportError:
        lat = -12.0464 + (utm_y - 8650000) / 111000
        lon = -77.0428 + (utm_x - 300000) / (111000 * 0.6)
        return lat, lon
    except Exception as e:
        print(f"Error en conversión UTM: {e}")
        return -12.0464, -77.0428

@router.get("/", response_model=Dict[str, OrigenResponse])
def obtener_origenes():
    """
    Obtiene los puntos de origen para Saga y Ripley.
    Estos son nodos hardcodeados pero reales del grafo de Lima.
    """
    grafo = grafo_wrapper.graph
    nodos_disponibles = list(grafo.Vertices)
    
    if len(nodos_disponibles) == 0:
        # Fallback si no hay nodos
        return {
            "Saga": OrigenResponse(
                nodo_id=0,
                nombre="Saga Falabella - Centro de Lima",
                latitud=-12.0464,
                longitud=-77.0428
            ),
            "Ripley": OrigenResponse(
                nodo_id=1,
                nombre="Ripley - Jockey Plaza",
                latitud=-12.0833,
                longitud=-76.9667
            )
        }
    
    # Seleccionar nodos FIJOS del grafo para Saga y Ripley (determinístico)
    # Ordenar nodos para asegurar consistencia
    nodos_disponibles_ordenados = sorted(nodos_disponibles)
    
    # Usar índices fijos para siempre obtener los mismos nodos
    # Nodo para Saga: índice 10% del total
    # Nodo para Ripley: índice 20% del total
    index_saga = int(len(nodos_disponibles_ordenados) * 0.1) if len(nodos_disponibles_ordenados) > 0 else 0
    index_ripley = int(len(nodos_disponibles_ordenados) * 0.2) if len(nodos_disponibles_ordenados) > 1 else 0
    
    nodo_saga = nodos_disponibles_ordenados[index_saga] if len(nodos_disponibles_ordenados) > index_saga else (nodos_disponibles_ordenados[0] if nodos_disponibles_ordenados else 0)
    nodo_ripley = nodos_disponibles_ordenados[index_ripley] if len(nodos_disponibles_ordenados) > index_ripley else (nodos_disponibles_ordenados[0] if nodos_disponibles_ordenados else 0)
    
    # Obtener coordenadas
    coords_saga_utm = grafo.get_node_coords(nodo_saga)
    coords_ripley_utm = grafo.get_node_coords(nodo_ripley)
    
    lat_saga, lon_saga = convertir_utm_a_latlon(coords_saga_utm[0], coords_saga_utm[1]) if coords_saga_utm != (0, 0) else (-12.0464, -77.0428)
    lat_ripley, lon_ripley = convertir_utm_a_latlon(coords_ripley_utm[0], coords_ripley_utm[1]) if coords_ripley_utm != (0, 0) else (-12.0833, -76.9667)
    
    return {
        "Saga": OrigenResponse(
            nodo_id=nodo_saga,
            nombre="Saga Falabella - Centro de Lima",
            latitud=lat_saga,
            longitud=lon_saga
        ),
        "Ripley": OrigenResponse(
            nodo_id=nodo_ripley,
            nombre="Ripley - Jockey Plaza",
            latitud=lat_ripley,
            longitud=lon_ripley
        )
    }

