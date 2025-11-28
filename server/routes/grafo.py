from fastapi import APIRouter
from typing import List
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models.grafo import NodoResponse, AristaResponse
from models.grafo_wrapper import grafo_wrapper

router = APIRouter()

def convertir_utm_a_latlon(utm_x: float, utm_y: float):
    """
    Convierte coordenadas UTM (Zone 18S, EPSG:32718) a lat/lon (WGS84, EPSG:4326)
    Lima, Perú está en UTM Zone 18S
    """
    try:
        from pyproj import Transformer
        
        # UTM Zone 18S para Lima, Perú (EPSG:32718)
        # WGS84 (EPSG:4326) para lat/lon
        transformer = Transformer.from_crs("EPSG:32718", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(utm_x, utm_y)
        return lat, lon
    except ImportError:
        # Si pyproj no está disponible, usar aproximación simple
        # Esta es una aproximación muy básica, no es precisa
        # Lima está aproximadamente en: lat -12.0464, lon -77.0428
        # UTM aproximado: x ~ 300000, y ~ 8650000
        # Factor de conversión aproximado
        lat = -12.0464 + (utm_y - 8650000) / 111000
        lon = -77.0428 + (utm_x - 300000) / (111000 * 0.6)
        return lat, lon
    except Exception as e:
        print(f"Error en conversión UTM: {e}")
        # Retornar coordenadas por defecto de Lima
        return -12.0464, -77.0428

@router.get("/nodos", response_model=List[NodoResponse])
def obtener_nodos():
    """Obtiene todos los nodos del grafo con sus coordenadas convertidas de UTM a lat/lon"""
    grafo = grafo_wrapper.graph
    nodos = []
    
    for nodo_id in grafo.Vertices:
        coords_utm = grafo.get_node_coords(nodo_id)
        # Las coordenadas vienen en UTM: (x, y) = (longitud_utm, latitud_utm)
        utm_x = coords_utm[0]  # longitud UTM
        utm_y = coords_utm[1]  # latitud UTM
        
        # Convertir de UTM a lat/lon
        lat, lon = convertir_utm_a_latlon(utm_x, utm_y)
        
        nodos.append(NodoResponse(
            id=nodo_id,
            latitud=lat,
            longitud=lon
        ))
    
    return nodos

@router.get("/aristas", response_model=List[AristaResponse])
def obtener_aristas():
    """Obtiene todas las aristas del grafo con sus pesos"""
    aristas = []
    
    for origen, destino, peso in grafo_wrapper.aristas:
        aristas.append(AristaResponse(
            origen=origen,
            destino=destino,
            peso=float(peso)
        ))
    
    return aristas

