from typing import List, Tuple
import sys
import os
import math
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models.grafo_wrapper import grafo_wrapper

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
        lat = -12.0464 + (utm_y - 8650000) / 111000
        lon = -77.0428 + (utm_x - 300000) / (111000 * 0.6)
        return lat, lon
    except Exception as e:
        print(f"Error en conversión UTM: {e}")
        return -12.0464, -77.0428

class RutaService:
    """Servicio para calcular rutas optimizadas"""
    
    def __init__(self):
        self.grafo = grafo_wrapper
        self._matriz = None
        self._nodo_to_idx = None
        self._idx_to_nodo = None
        self._inicializar_matriz()
    
    def _inicializar_matriz(self):
        """Inicializa la matriz de adyacencia una sola vez"""
        if self._matriz is None:
            self._matriz, self._nodo_to_idx = self.grafo.get_matriz_adyacencia()
            self._idx_to_nodo = {idx: nodo for nodo, idx in self._nodo_to_idx.items()}
            print(f"✅ Matriz de adyacencia inicializada con {len(self._nodo_to_idx)} nodos")
            print(f"   Primeros 10 nodos en la matriz: {list(self._nodo_to_idx.keys())[:10]}")
            print(f"   Últimos 10 nodos en la matriz: {list(self._nodo_to_idx.keys())[-10:]}")
    
    def calcular_ruta_optimizada(self, nodos: List[int]) -> Tuple[List[int], float, List[Tuple[float, float]]]:
        """
        Calcula la ruta optimizada para una lista de nodos usando TSP.
        
        Args:
            nodos: Lista de IDs de nodos a visitar
        
        Returns:
            Tupla (ruta_optimizada, distancia_total, coordenadas)
        """
        from algorithms.tsp import solve_tsp
        
        if not nodos:
            return [], 0.0, []
        
        # Resolver TSP
        ruta_optimizada, distancia_total = solve_tsp(
            self._matriz,
            nodos,
            self._nodo_to_idx,
            self._idx_to_nodo
        )
        
        # Obtener coordenadas para cada nodo en la ruta
        coordenadas = []
        for nodo_id in ruta_optimizada:
            coords_utm = self.grafo.graph.get_node_coords(nodo_id)
            # Convertir de UTM a lat/lon
            lat, lon = convertir_utm_a_latlon(coords_utm[0], coords_utm[1])
            # Formato [latitud, longitud] para Leaflet
            coordenadas.append((lat, lon))
        
        return ruta_optimizada, distancia_total, coordenadas
    
    def _calcular_ruta_grafo_directo(self, origen: int, destino: int) -> Tuple[List[int], float]:
        """
        Calcula la ruta entre dos nodos usando Dijkstra sobre la estructura del grafo directamente.
        Esto garantiza que encuentra el camino MÁS CORTO pasando por TODOS los nodos intermedios necesarios.
        
        Args:
            origen: ID del nodo origen
            destino: ID del nodo destino
        
        Returns:
            Tupla (ruta, distancia_total) donde ruta es lista de IDs de nodos incluyendo TODOS los intermedios
        """
        import heapq
        
        if origen not in self.grafo.graph.label2v or destino not in self.grafo.graph.label2v:
            print(f"      ❌ Origen ({origen}) o Destino ({destino}) no encontrado en el grafo.")
            return [], float('inf')
        
        # Dijkstra sobre el grafo directamente para encontrar el camino más corto con TODOS los nodos intermedios
        distancias = {origen: 0.0}
        previos = {origen: None}
        visitados = set()
        cola = [(0.0, origen)]
        
        # Verificar que los nodos existen y tienen vecinos
        vecinos_origen = self.grafo.graph.get_children(origen)
        padres_origen = self.grafo.graph.get_parents(origen)
        todos_vecinos_origen = set(vecinos_origen + padres_origen)
        
        print(f"      Iniciando Dijkstra sobre el grafo desde nodo {origen} hacia nodo {destino}")
        print(f"         Vecinos del origen ({origen}): {len(todos_vecinos_origen)} nodos")
        if len(todos_vecinos_origen) > 0:
            print(f"         Primeros vecinos: {list(todos_vecinos_origen)[:5]}")
        
        vecinos_destino = self.grafo.graph.get_children(destino)
        padres_destino = self.grafo.graph.get_parents(destino)
        todos_vecinos_destino = set(vecinos_destino + padres_destino)
        print(f"         Vecinos del destino ({destino}): {len(todos_vecinos_destino)} nodos")
        
        max_iteraciones = 10000
        iteraciones = 0
        
        while cola and iteraciones < max_iteraciones:
            iteraciones += 1
            dist_actual, nodo_actual = heapq.heappop(cola)
            
            if nodo_actual in visitados:
                continue
                
            visitados.add(nodo_actual)
            
            # Si llegamos al destino, reconstruir el camino completo
            if nodo_actual == destino:
                camino = []
                nodo = destino
                while nodo is not None:
                    camino.append(nodo)
                    nodo = previos[nodo]
                camino.reverse()
                
                # Calcular distancia total sumando distancias entre nodos consecutivos
                distancia_total = 0.0
                for i in range(len(camino) - 1):
                    coords1 = self.grafo.graph.get_node_coords(camino[i])
                    coords2 = self.grafo.graph.get_node_coords(camino[i + 1])
                    if coords1 and coords2 and coords1 != (0, 0) and coords2 != (0, 0):
                        dist = math.sqrt((coords1[0] - coords2[0])**2 + (coords1[1] - coords2[1])**2)
                        distancia_total += dist
                
                print(f"      ✅ Dijkstra sobre grafo encontró camino con {len(camino)} nodos (TODOS los intermedios)")
                print(f"         Camino completo: {camino[:10]}..." + (f" (total: {len(camino)} nodos)" if len(camino) > 10 else ""))
                return camino, distancia_total
            
            # Obtener vecinos del nodo actual usando la estructura del grafo
            vecinos = self.grafo.graph.get_children(nodo_actual)
            padres = self.grafo.graph.get_parents(nodo_actual)
            todos_vecinos = set(vecinos + padres)
            
            if len(todos_vecinos) == 0:
                # Nodo sin conexiones, saltarlo
                continue
            
            for vecino in todos_vecinos:
                if vecino in visitados:
                    continue
                
                # Calcular distancia al vecino
                coords_actual = self.grafo.graph.get_node_coords(nodo_actual)
                coords_vecino = self.grafo.graph.get_node_coords(vecino)
                
                if coords_actual and coords_vecino and coords_actual != (0, 0) and coords_vecino != (0, 0):
                    dist = math.sqrt((coords_actual[0] - coords_vecino[0])**2 + (coords_actual[1] - coords_vecino[1])**2)
                    nueva_dist = dist_actual + dist
                    
                    if vecino not in distancias or nueva_dist < distancias[vecino]:
                        distancias[vecino] = nueva_dist
                        previos[vecino] = nodo_actual
                        heapq.heappush(cola, (nueva_dist, vecino))
        
        if iteraciones >= max_iteraciones:
            print(f"      ⚠️ Dijkstra alcanzó el límite de iteraciones ({max_iteraciones})")
        
        # No se encontró camino
        print(f"      ❌ Dijkstra sobre grafo no encontró camino después de explorar {len(visitados)} nodos")
        print(f"         Nodos explorados: {len(visitados)}")
        print(f"         ¿Origen y destino están en el mismo componente conectado?")
        return [], float('inf')
    
    def calcular_ruta_entre_nodos(self, origen: int, destino: int, algoritmo: str = "dijkstra") -> Tuple[List[int], float, List[Tuple[float, float]]]:
        """
        Calcula la ruta más corta entre dos nodos usando el algoritmo especificado.
        
        Args:
            origen: ID del nodo origen
            destino: ID del nodo destino
            algoritmo: Algoritmo a usar ("dijkstra" o "floyd_warshall")
        
        Returns:
            Tupla (ruta, distancia_total, coordenadas) donde ruta es lista de IDs de nodos
        """
        print(f"Calculando ruta de punto A a punto B: {origen} -> {destino} usando {algoritmo.upper()}")
        
        if algoritmo.lower() == "floyd_warshall":
            return self._calcular_ruta_floyd_warshall(origen, destino)
        else:
            return self._calcular_ruta_dijkstra(origen, destino)
    
    def _calcular_ruta_dijkstra(self, origen: int, destino: int) -> Tuple[List[int], float, List[Tuple[float, float]]]:
        """Calcula la ruta usando el algoritmo de Dijkstra"""
        from algorithms.dijkstra import dijkstra
        
        if origen not in self._nodo_to_idx or destino not in self._nodo_to_idx:
            print(f"      ❌ Origen ({origen}) o Destino ({destino}) no encontrado en la matriz.")
            return [], 0.0, []
        
        origen_idx = self._nodo_to_idx[origen]
        destino_idx = self._nodo_to_idx[destino]
        
        # Usar Dijkstra sobre la matriz
        distancia_total, camino_indices = dijkstra(self._matriz, origen_idx, destino_idx)
        
        if not camino_indices:
            print(f"      ❌ Dijkstra no encontró camino")
            # Intentar con el método directo del grafo
            camino_nodos, distancia_directa = self._calcular_ruta_grafo_directo(origen, destino)
            if camino_nodos:
                coordenadas = self._obtener_coordenadas_ruta(camino_nodos)
                return camino_nodos, distancia_directa, coordenadas
            return [], 0.0, []
        
        # Convertir índices de vuelta a IDs de nodos
        camino_nodos = [self._idx_to_nodo[idx] for idx in camino_indices]
        
        print(f"      ✅ Dijkstra encontró camino con {len(camino_nodos)} nodos")
        
        # Verificar si el camino del grafo real tiene más nodos intermedios
        print(f"         Verificando si el camino del grafo real tiene más nodos intermedios...")
        camino_grafo, distancia_grafo = self._calcular_ruta_grafo_directo(origen, destino)
        
        if camino_grafo and len(camino_grafo) > len(camino_nodos):
            print(f"      ✅ Usando camino del grafo con {len(camino_grafo)} nodos (más detallado)")
            coordenadas = self._obtener_coordenadas_ruta(camino_grafo)
            return camino_grafo, distancia_grafo, coordenadas
        else:
            coordenadas = self._obtener_coordenadas_ruta(camino_nodos)
            return camino_nodos, distancia_total, coordenadas
    
    def _calcular_ruta_floyd_warshall(self, origen: int, destino: int) -> Tuple[List[int], float, List[Tuple[float, float]]]:
        """Calcula la ruta usando el algoritmo de Floyd-Warshall"""
        from algorithms.floyd_warshall import encontrar_camino_floyd_warshall
        
        if origen not in self._nodo_to_idx or destino not in self._nodo_to_idx:
            print(f"      ❌ Origen ({origen}) o Destino ({destino}) no encontrado en la matriz.")
            return [], 0.0, []
        
        origen_idx = self._nodo_to_idx[origen]
        destino_idx = self._nodo_to_idx[destino]
        
        # Usar Floyd-Warshall sobre la matriz
        distancia_total, camino_indices = encontrar_camino_floyd_warshall(self._matriz, origen_idx, destino_idx)
        
        if not camino_indices:
            print(f"      ❌ Floyd-Warshall no encontró camino")
            return [], 0.0, []
        
        # Convertir índices de vuelta a IDs de nodos
        camino_nodos = [self._idx_to_nodo[idx] for idx in camino_indices]
        
        print(f"      ✅ Floyd-Warshall encontró camino con {len(camino_nodos)} nodos")
        print(f"         Camino: {camino_nodos[:10]}..." + (f" (total: {len(camino_nodos)})" if len(camino_nodos) > 10 else ""))
        
        # Obtener coordenadas
        coordenadas = self._obtener_coordenadas_ruta(camino_nodos)
        return camino_nodos, distancia_total, coordenadas
    
    def _obtener_coordenadas_ruta(self, camino_nodos: List[int]) -> List[Tuple[float, float]]:
        """Obtiene las coordenadas de una ruta de nodos"""
        coordenadas = []
        for nodo_id in camino_nodos:
            coords_utm = self.grafo.graph.get_node_coords(nodo_id)
            lat, lon = convertir_utm_a_latlon(coords_utm[0], coords_utm[1])
            coordenadas.append((lat, lon))
        
        print(f"      ✅ Coordenadas obtenidas: {len(coordenadas)} puntos para ruta de {len(camino_nodos)} nodos")
        if len(coordenadas) >= 3:
            print(f"         Primeros 3 puntos: {coordenadas[:3]}")
            print(f"         Últimos 3 puntos: {coordenadas[-3:]}")
        
        return coordenadas
        """
        Calcula la ruta más corta entre dos nodos pasando por TODOS los nodos intermedios del grafo.
        Usa BFS sobre el grafo directamente para garantizar que pasa por todos los nodos del camino real.
        
        Args:
            origen: ID del nodo origen
            destino: ID del nodo destino
        
        Returns:
            Tupla (ruta, distancia_total, coordenadas) donde ruta incluye TODOS los nodos intermedios
        """
        from algorithms.dijkstra import dijkstra
        
        # Primero intentar con Dijkstra si los nodos están en la matriz para obtener la distancia
        distancia_estimada = float('inf')
        if origen in self._nodo_to_idx and destino in self._nodo_to_idx:
            origen_idx = self._nodo_to_idx[origen]
            destino_idx = self._nodo_to_idx[destino]
            
            distancia_estimada, camino_indices = dijkstra(self._matriz, origen_idx, destino_idx)
            
            if camino_indices and len(camino_indices) > 2:
                # Si Dijkstra encontró un camino con nodos intermedios, verificar si coincide con el grafo real
                ruta_dijkstra = [self._idx_to_nodo[idx] for idx in camino_indices]
                print(f"      ✅ Dijkstra encontró camino con {len(ruta_dijkstra)} nodos")
                print(f"         Verificando si el camino del grafo real tiene más nodos intermedios...")
        
        # SIEMPRE usar Dijkstra sobre el grafo directamente para obtener el camino MÁS CORTO con TODOS los nodos intermedios
        print(f"   Calculando ruta {origen} -> {destino} usando Dijkstra sobre el grafo (garantiza camino más corto con todos los nodos intermedios)")
        ruta, distancia_total = self._calcular_ruta_grafo_directo(origen, destino)
        
        if ruta:
            print(f"      ✅ Dijkstra sobre grafo encontró ruta con {len(ruta)} nodos: {ruta[:5]}..." + (f" (total: {len(ruta)})" if len(ruta) > 5 else ""))
        else:
            print(f"      ❌ Dijkstra sobre grafo no encontró ruta entre {origen} y {destino}")
        
        if not ruta:
            # Último fallback: línea recta si tienen coordenadas válidas
            coords_origen_utm = self.grafo.graph.get_node_coords(origen)
            coords_destino_utm = self.grafo.graph.get_node_coords(destino)
            
            if coords_origen_utm and coords_origen_utm != (0, 0) and coords_destino_utm and coords_destino_utm != (0, 0):
                lat_origen, lon_origen = convertir_utm_a_latlon(coords_origen_utm[0], coords_origen_utm[1])
                lat_destino, lon_destino = convertir_utm_a_latlon(coords_destino_utm[0], coords_destino_utm[1])
                
                dlat = lat_destino - lat_origen
                dlon = lon_destino - lon_origen
                distancia_aprox = math.sqrt(dlat**2 + dlon**2) * 111.0
                
                return [origen, destino], distancia_aprox, [(lat_origen, lon_origen), (lat_destino, lon_destino)]
            
            return [], float('inf'), []
        
        # Obtener coordenadas de la ruta encontrada con BFS
        coordenadas = []
        for nodo_id in ruta:
            coords_utm = self.grafo.graph.get_node_coords(nodo_id)
            if coords_utm and coords_utm != (0, 0):
                lat, lon = convertir_utm_a_latlon(coords_utm[0], coords_utm[1])
                coordenadas.append((lat, lon))
        
        print(f"      ✅ Coordenadas obtenidas: {len(coordenadas)} puntos para ruta de {len(ruta)} nodos")
        if len(coordenadas) > 2:
            print(f"         Primeros 3 puntos: {coordenadas[:3]}")
            print(f"         Últimos 3 puntos: {coordenadas[-3:]}")
        
        return ruta, distancia_total, coordenadas
    
    def calcular_ruta_completa_con_segmentos(self, nodos: List[int]) -> Tuple[List[int], float, List[List[Tuple[float, float]]]]:
        """
        Calcula la ruta optimizada y luego el camino real en el grafo entre cada par de nodos consecutivos.
        
        Args:
            nodos: Lista de IDs de nodos a visitar
        
        Returns:
            Tupla (ruta_optimizada, distancia_total, segmentos)
            donde segmentos es una lista de listas de coordenadas, cada una representa
            el camino real en el grafo entre dos nodos consecutivos
        """
        from algorithms.tsp import solve_tsp
        
        if not nodos:
            return [], 0.0, []
        
        # Verificar qué nodos están en la matriz
        nodos_en_matriz = [nodo for nodo in nodos if nodo in self._nodo_to_idx]
        nodos_faltantes = [nodo for nodo in nodos if nodo not in self._nodo_to_idx]
        if nodos_faltantes:
            print(f"⚠️ ADVERTENCIA RutaService: {len(nodos_faltantes)} nodos del pedido no están en la matriz: {nodos_faltantes}")
            print(f"   Nodos solicitados: {nodos}")
            print(f"   Nodos encontrados en matriz: {nodos_en_matriz}")
            print(f"   Total de nodos en matriz: {len(self._nodo_to_idx)}")
            # Mostrar algunos ejemplos de nodos que SÍ están en la matriz
            ejemplos = list(self._nodo_to_idx.keys())[:5]
            print(f"   Ejemplos de nodos en matriz: {ejemplos}")
        
        # Si el primer y último nodo son iguales, es un origen fijo
        origen_fijo = None
        if len(nodos) > 1 and nodos[0] == nodos[-1]:
            origen_fijo = nodos[0]
            # Remover el último nodo (duplicado) para el TSP
            nodos_para_tsp = nodos[:-1]
        else:
            nodos_para_tsp = nodos
        
        # Resolver TSP para obtener el orden optimizado
        ruta_optimizada, distancia_total = solve_tsp(
            self._matriz,
            nodos_para_tsp,
            self._nodo_to_idx,
            self._idx_to_nodo,
            origen_fijo=origen_fijo
        )
        
        # Calcular el camino real en el grafo entre cada par de nodos consecutivos
        segmentos = []
        distancia_total_real = 0.0
        
        # Para cada par de nodos consecutivos en la ruta optimizada
        for i in range(len(ruta_optimizada) - 1):
            origen = ruta_optimizada[i]
            destino = ruta_optimizada[i + 1]
            
            # Calcular el camino real entre estos dos nodos usando Dijkstra
            _, distancia_segmento, coordenadas_segmento = self.calcular_ruta_entre_nodos(origen, destino)
            
            if coordenadas_segmento and len(coordenadas_segmento) > 0:
                # Si hay un camino válido, agregarlo
                segmentos.append(coordenadas_segmento)
                if distancia_segmento != float('inf'):
                    distancia_total_real += distancia_segmento
            else:
                # Si no hay camino directo en el grafo, usar línea recta como fallback
                coords_origen_utm = self.grafo.graph.get_node_coords(origen)
                coords_destino_utm = self.grafo.graph.get_node_coords(destino)
                
                if coords_origen_utm and coords_destino_utm:
                    lat_origen, lon_origen = convertir_utm_a_latlon(coords_origen_utm[0], coords_origen_utm[1])
                    lat_destino, lon_destino = convertir_utm_a_latlon(coords_destino_utm[0], coords_destino_utm[1])
                    segmentos.append([(lat_origen, lon_origen), (lat_destino, lon_destino)])
                    # Aproximación de distancia para línea recta (Haversine simplificado)
                    distancia_total_real += distancia_total / len(ruta_optimizada) if len(ruta_optimizada) > 0 else 0
        
        # Si no hay segmentos, usar la distancia del TSP
        if distancia_total_real == 0.0:
            distancia_total_real = distancia_total
        
        return ruta_optimizada, distancia_total_real, segmentos

