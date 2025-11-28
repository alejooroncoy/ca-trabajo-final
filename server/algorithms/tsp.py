from typing import List, Tuple
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from algorithms.dijkstra import dijkstra

def solve_tsp(matriz_adyacencia: List[List[float]], nodos_a_visitar: List[int], 
              nodo_to_idx: dict, idx_to_nodo: dict, origen_fijo: int = None) -> Tuple[List[int], float]:
    """
    Resuelve el problema del agente viajero (TSP) usando heurística Nearest Neighbor + 2-opt.
    Si se especifica origen_fijo, la ruta comenzará y terminará en ese nodo.
    
    Args:
        matriz_adyacencia: Matriz de adyacencia con pesos
        nodos_a_visitar: Lista de IDs de nodos que deben ser visitados
        nodo_to_idx: Diccionario que mapea ID de nodo a índice en la matriz
        idx_to_nodo: Diccionario que mapea índice en la matriz a ID de nodo
        origen_fijo: Nodo que debe ser el inicio y fin de la ruta (opcional)
    
    Returns:
        Tupla (ruta_optimizada, distancia_total)
    """
    if len(nodos_a_visitar) == 0:
        return [], 0.0
    
    if len(nodos_a_visitar) == 1:
        return nodos_a_visitar, 0.0
    
    # Si hay origen fijo, asegurar que esté en la lista y sea el primero
    nodos_para_visitar = nodos_a_visitar.copy()
    if origen_fijo is not None and origen_fijo in nodos_para_visitar:
        # Remover el origen de la lista (se agregará al inicio y final)
        nodos_para_visitar = [n for n in nodos_para_visitar if n != origen_fijo]
        if len(nodos_para_visitar) == 0:
            # Solo el origen, retornar [origen, origen]
            return [origen_fijo, origen_fijo], 0.0
    elif origen_fijo is not None:
        # Si el origen no está en la lista, agregarlo
        nodos_para_visitar.insert(0, origen_fijo)
    
    # Convertir nodos a índices
    indices = [nodo_to_idx[nodo] for nodo in nodos_para_visitar if nodo in nodo_to_idx]
    
    # Logging para depuración
    nodos_no_encontrados = [nodo for nodo in nodos_para_visitar if nodo not in nodo_to_idx]
    if nodos_no_encontrados:
        print(f"⚠️ ADVERTENCIA TSP: {len(nodos_no_encontrados)} nodos no encontrados en la matriz: {nodos_no_encontrados}")
        print(f"   Nodos a visitar: {nodos_para_visitar}")
        print(f"   Nodos encontrados: {len(indices)} de {len(nodos_para_visitar)}")
    
    if len(indices) == 0:
        print("⚠️ ERROR TSP: No se encontraron nodos válidos en la matriz")
        return [], 0.0
    
    if len(indices) == 1:
        print(f"⚠️ ADVERTENCIA TSP: Solo se encontró 1 nodo válido de {len(nodos_para_visitar)} nodos solicitados")
        nodo_unico = idx_to_nodo[indices[0]]
        if origen_fijo is not None:
            return [origen_fijo, nodo_unico, origen_fijo], 0.0
        return [nodo_unico], 0.0
    
    # Si hay origen fijo, comenzar desde ese nodo
    if origen_fijo is not None and origen_fijo in nodo_to_idx:
        origen_idx = nodo_to_idx[origen_fijo]
        # Asegurar que el origen esté al inicio
        if origen_idx in indices:
            indices.remove(origen_idx)
        ruta = _nearest_neighbor_desde_origen(matriz_adyacencia, indices, origen_idx)
    else:
        # Heurística Nearest Neighbor normal
        ruta = _nearest_neighbor(matriz_adyacencia, indices)
    
    # Mejora con 2-opt
    ruta = _two_opt(matriz_adyacencia, ruta)
    
    # Convertir índices de vuelta a IDs de nodos
    ruta_nodos = [idx_to_nodo[idx] for idx in ruta]
    
    # Si hay origen fijo, agregarlo al inicio y final
    if origen_fijo is not None:
        if ruta_nodos[0] != origen_fijo:
            ruta_nodos.insert(0, origen_fijo)
        if ruta_nodos[-1] != origen_fijo:
            ruta_nodos.append(origen_fijo)
    
    # Calcular distancia total
    distancia_total = _calcular_distancia_total(matriz_adyacencia, ruta)
    
    # Si hay origen fijo, agregar distancia de retorno
    if origen_fijo is not None and len(ruta_nodos) > 1:
        origen_idx = nodo_to_idx[origen_fijo]
        ultimo_idx = nodo_to_idx[ruta_nodos[-2]] if ruta_nodos[-2] in nodo_to_idx else None
        if ultimo_idx is not None:
            dist_retorno = matriz_adyacencia[ultimo_idx][origen_idx]
            if dist_retorno != float('inf'):
                distancia_total += dist_retorno
    
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

def _nearest_neighbor_desde_origen(matriz_adyacencia: List[List[float]], indices: List[int], origen_idx: int) -> List[int]:
    """Heurística del vecino más cercano comenzando desde un origen fijo"""
    if len(indices) == 0:
        return [origen_idx]
    
    ruta = [origen_idx]
    no_visitados = set(indices)
    
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

