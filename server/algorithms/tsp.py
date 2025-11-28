from typing import List, Tuple
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from algorithms.dijkstra import dijkstra

def solve_tsp(matriz_adyacencia: List[List[float]], nodos_a_visitar: List[int], 
              nodo_to_idx: dict, idx_to_nodo: dict) -> Tuple[List[int], float]:
    """
    Resuelve el problema del agente viajero (TSP) usando heurística Nearest Neighbor + 2-opt.
    
    Args:
        matriz_adyacencia: Matriz de adyacencia con pesos
        nodos_a_visitar: Lista de IDs de nodos que deben ser visitados
        nodo_to_idx: Diccionario que mapea ID de nodo a índice en la matriz
        idx_to_nodo: Diccionario que mapea índice en la matriz a ID de nodo
    
    Returns:
        Tupla (ruta_optimizada, distancia_total)
    """
    if len(nodos_a_visitar) == 0:
        return [], 0.0
    
    if len(nodos_a_visitar) == 1:
        return nodos_a_visitar, 0.0
    
    # Convertir nodos a índices
    indices = [nodo_to_idx[nodo] for nodo in nodos_a_visitar if nodo in nodo_to_idx]
    
    # Logging para depuración
    nodos_no_encontrados = [nodo for nodo in nodos_a_visitar if nodo not in nodo_to_idx]
    if nodos_no_encontrados:
        print(f"⚠️ ADVERTENCIA TSP: {len(nodos_no_encontrados)} nodos no encontrados en la matriz: {nodos_no_encontrados}")
        print(f"   Nodos a visitar: {nodos_a_visitar}")
        print(f"   Nodos encontrados: {len(indices)} de {len(nodos_a_visitar)}")
    
    if len(indices) == 0:
        print("⚠️ ERROR TSP: No se encontraron nodos válidos en la matriz")
        return [], 0.0
    
    if len(indices) == 1:
        print(f"⚠️ ADVERTENCIA TSP: Solo se encontró 1 nodo válido de {len(nodos_a_visitar)} nodos solicitados")
        return [idx_to_nodo[indices[0]]], 0.0
    
    # Heurística Nearest Neighbor
    ruta = _nearest_neighbor(matriz_adyacencia, indices)
    
    # Mejora con 2-opt
    ruta = _two_opt(matriz_adyacencia, ruta)
    
    # Convertir índices de vuelta a IDs de nodos
    ruta_nodos = [idx_to_nodo[idx] for idx in ruta]
    
    # Calcular distancia total
    distancia_total = _calcular_distancia_total(matriz_adyacencia, ruta)
    
    return ruta_nodos, distancia_total

def _nearest_neighbor(matriz_adyacencia: List[List[float]], indices: List[int]) -> List[int]:
    """Heurística del vecino más cercano"""
    if len(indices) <= 1:
        return indices
    
    ruta = [indices[0]]
    no_visitados = set(indices[1:])
    
    while no_visitados:
        ultimo = ruta[-1]
        mas_cercano = None
        menor_dist = float('inf')
        
        for vecino in no_visitados:
            dist = matriz_adyacencia[ultimo][vecino]
            if dist < menor_dist:
                menor_dist = dist
                mas_cercano = vecino
        
        if mas_cercano is not None:
            ruta.append(mas_cercano)
            no_visitados.remove(mas_cercano)
        else:
            # Si no hay conexión, agregar el más cercano por distancia euclidiana
            break
    
    return ruta

def _two_opt(matriz_adyacencia: List[List[float]], ruta: List[int]) -> List[int]:
    """Mejora la ruta usando 2-opt"""
    mejor_ruta = ruta[:]
    mejor_dist = _calcular_distancia_total(matriz_adyacencia, mejor_ruta)
    mejorado = True
    
    while mejorado:
        mejorado = False
        for i in range(1, len(mejor_ruta) - 2):
            for j in range(i + 1, len(mejor_ruta)):
                if j - i == 1:
                    continue
                
                # Intentar swap
                nueva_ruta = mejor_ruta[:]
                nueva_ruta[i:j] = reversed(nueva_ruta[i:j])
                nueva_dist = _calcular_distancia_total(matriz_adyacencia, nueva_ruta)
                
                if nueva_dist < mejor_dist:
                    mejor_ruta = nueva_ruta
                    mejor_dist = nueva_dist
                    mejorado = True
    
    return mejor_ruta

def _calcular_distancia_total(matriz_adyacencia: List[List[float]], ruta: List[int]) -> float:
    """Calcula la distancia total de una ruta"""
    if len(ruta) <= 1:
        return 0.0
    
    distancia = 0.0
    for i in range(len(ruta) - 1):
        dist = matriz_adyacencia[ruta[i]][ruta[i + 1]]
        if dist == float('inf'):
            # Si no hay conexión directa, usar distancia euclidiana aproximada
            distancia += 100.0  # Penalización
        else:
            distancia += dist
    
    return distancia

