"""
Servicio para calcular rutas reales usando OSRM (Open Source Routing Machine)
OSRM usa datos de OpenStreetMap y calcula rutas que siguen las calles reales
"""
from typing import List, Tuple, Optional
import requests
import math

class OSRMService:
    """Servicio para calcular rutas usando OSRM"""
    
    # URL del servidor OSRM público (puedes usar uno local si lo prefieres)
    # Para Lima, Perú, usamos un servidor público de OSRM
    BASE_URL = "http://router.project-osrm.org/route/v1/driving"
    
    @staticmethod
    def calcular_ruta_entre_puntos(
        origen: Tuple[float, float],  # (lat, lon)
        destino: Tuple[float, float],  # (lat, lon)
        pasos_intermedios: bool = True,
        numero_alternativas: int = 0
    ) -> Optional[Tuple[List[Tuple[float, float]], float]]:
        """
        Calcula la ruta real entre dos puntos usando OSRM.
        
        Args:
            origen: Tupla (latitud, longitud) del punto origen
            destino: Tupla (latitud, longitud) del punto destino
            pasos_intermedios: Si True, devuelve todos los puntos intermedios de la ruta
        
        Returns:
            Tupla (coordenadas, distancia_km) o None si hay error
            coordenadas: Lista de tuplas (lat, lon) que forman la ruta
        """
        try:
            # OSRM usa formato lon,lat (no lat,lon)
            lon_origen, lat_origen = origen[1], origen[0]
            lon_destino, lat_destino = destino[1], destino[0]
            
            # Construir URL para OSRM
            url = f"{OSRMService.BASE_URL}/{lon_origen},{lat_origen};{lon_destino},{lat_destino}"
            params = {
                "overview": "full",  # Siempre usar 'full' para máxima precisión
                "geometries": "geojson",
                "steps": "true",  # Incluir pasos intermedios para mayor precisión
                "alternatives": str(numero_alternativas)
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"Error OSRM: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            
            if data.get("code") != "Ok" or not data.get("routes"):
                print(f"Error OSRM: {data.get('message', 'Ruta no encontrada')}")
                return None
            
            route = data["routes"][0]
            distancia_metros = route["distance"]
            distancia_km = distancia_metros / 1000.0
            
            # Extraer coordenadas de la geometría
            geometry = route["geometry"]["coordinates"]
            coordenadas = [(coord[1], coord[0]) for coord in geometry]  # Convertir de [lon, lat] a (lat, lon)
            
            return coordenadas, distancia_km
            
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión con OSRM: {e}")
            return None
        except Exception as e:
            print(f"Error al calcular ruta con OSRM: {e}")
            return None
    
    @staticmethod
    def calcular_ruta_multiple(
        puntos: List[Tuple[float, float]],  # Lista de (lat, lon)
        optimizar_orden: bool = False
    ) -> Optional[Tuple[List[Tuple[float, float]], float]]:
        """
        Calcula una ruta que pasa por múltiples puntos.
        
        Args:
            puntos: Lista de tuplas (latitud, longitud)
            optimizar_orden: Si True, OSRM optimiza el orden (TSP aproximado)
        
        Returns:
            Tupla (coordenadas_completas, distancia_total_km) o None
        """
        if len(puntos) < 2:
            return None
        
        try:
            # Construir URL con todos los puntos
            coordenadas_str = ";".join([f"{lon},{lat}" for lat, lon in puntos])
            url = f"{OSRMService.BASE_URL}/{coordenadas_str}"
            
            params = {
                "overview": "full",
                "geometries": "geojson",
                "steps": "true"
            }
            
            if optimizar_orden and len(puntos) > 2:
                params["roundtrip"] = "false"
                # OSRM tiene soporte limitado para TSP, mejor lo hacemos nosotros
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"Error OSRM múltiple: {response.status_code}")
                # Fallback: calcular segmento por segmento
                return OSRMService._calcular_ruta_segmentos(puntos)
            
            data = response.json()
            
            if data.get("code") != "Ok" or not data.get("routes"):
                # Fallback: calcular segmento por segmento
                return OSRMService._calcular_ruta_segmentos(puntos)
            
            route = data["routes"][0]
            distancia_metros = route["distance"]
            distancia_km = distancia_metros / 1000.0
            
            # Extraer coordenadas
            geometry = route["geometry"]["coordinates"]
            coordenadas = [(coord[1], coord[0]) for coord in geometry]
            
            return coordenadas, distancia_km
            
        except Exception as e:
            print(f"Error en ruta múltiple OSRM: {e}")
            # Fallback: calcular segmento por segmento
            return OSRMService._calcular_ruta_segmentos(puntos)
    
    @staticmethod
    def _calcular_ruta_segmentos(
        puntos: List[Tuple[float, float]]
    ) -> Optional[Tuple[List[Tuple[float, float]], float]]:
        """
        Calcula la ruta segmento por segmento (fallback).
        """
        todas_coordenadas: List[Tuple[float, float]] = []
        distancia_total = 0.0
        
        for i in range(len(puntos) - 1):
            resultado = OSRMService.calcular_ruta_entre_puntos(
                puntos[i],
                puntos[i + 1],
                pasos_intermedios=True
            )
            
            if resultado:
                coordenadas, distancia = resultado
                # Evitar duplicar el último punto
                if todas_coordenadas and coordenadas:
                    if todas_coordenadas[-1] == coordenadas[0]:
                        todas_coordenadas.extend(coordenadas[1:])
                    else:
                        todas_coordenadas.extend(coordenadas)
                else:
                    todas_coordenadas.extend(coordenadas)
                
                distancia_total += distancia
            else:
                # Si falla un segmento, usar línea recta como fallback
                todas_coordenadas.append(puntos[i])
                todas_coordenadas.append(puntos[i + 1])
                # Calcular distancia aproximada
                distancia_total += OSRMService._distancia_haversine(puntos[i], puntos[i + 1])
        
        return todas_coordenadas, distancia_total
    
    @staticmethod
    def _distancia_haversine(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calcula distancia entre dos puntos usando fórmula de Haversine (km)"""
        R = 6371  # Radio de la Tierra en km
        
        lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
        lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c

