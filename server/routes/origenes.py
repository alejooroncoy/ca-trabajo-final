from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List
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
    
    # Seleccionar nodos en Lima CENTRAL para Saga y Ripley
    # Lima central está alrededor de: -12.0464, -77.0428
    lima_centro_lat = -12.0464
    lima_centro_lon = -77.0428
    
    def obtener_nodos_por_zona(lat_centro: float, lon_centro: float, radio_km: float = 3.0) -> List[int]:
        """Obtiene nodos cerca del centro de Lima"""
        from services.ruta_service import convertir_utm_a_latlon
        import math
        
        nodos_en_zona = []
        for nodo_id in nodos_disponibles:
            coords_utm = grafo.get_node_coords(nodo_id)
            if coords_utm and coords_utm != (0, 0):
                lat, lon = convertir_utm_a_latlon(coords_utm[0], coords_utm[1])
                
                # Calcular distancia usando Haversine
                R = 6371  # Radio de la Tierra en km
                lat1, lon1 = math.radians(lat_centro), math.radians(lon_centro)
                lat2, lon2 = math.radians(lat), math.radians(lon)
                
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                
                a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                distancia = R * c
                
                if distancia <= radio_km:
                    nodos_en_zona.append((nodo_id, distancia, lat, lon))
        
        # Ordenar por distancia al centro
        nodos_en_zona.sort(key=lambda x: x[1])
        return [nodo[0] for nodo in nodos_en_zona]
    
    # Obtener nodos en Lima central (dentro de 3 km del centro)
    nodos_lima_central = obtener_nodos_por_zona(lima_centro_lat, lima_centro_lon, radio_km=3.0)
    
    if len(nodos_lima_central) >= 2:
        # Saga: primer nodo más cercano al centro
        # Ripley: segundo nodo más cercano al centro (separados pero ambos en el centro)
        nodo_saga = nodos_lima_central[0]
        nodo_ripley = nodos_lima_central[1] if len(nodos_lima_central) > 1 else nodos_lima_central[0]
        print(f"Saga y Ripley en Lima central - Nodos: {nodo_saga}, {nodo_ripley}")
    else:
        # Fallback: usar nodos ordenados
        nodos_ordenados = sorted(nodos_disponibles)
        nodo_saga = nodos_ordenados[0] if nodos_ordenados else 0
        nodo_ripley = nodos_ordenados[1] if len(nodos_ordenados) > 1 else nodo_saga
        print(f"Fallback: usando primeros nodos ordenados")
    
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

