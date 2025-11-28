import heapq
from typing import List, Tuple, Dict

def dijkstra(matriz_adyacencia: List[List[float]], inicio_idx: int, fin_idx: int) -> Tuple[float, List[int]]:
    """
    Algoritmo de Dijkstra para encontrar el camino más corto entre dos nodos.
    
    Args:
        matriz_adyacencia: Matriz de adyacencia con pesos
        inicio_idx: Índice del nodo inicial
        fin_idx: Índice del nodo destino
    
    Returns:
        Tupla (distancia_total, camino) donde camino es lista de índices
    """
    n = len(matriz_adyacencia)
    distancias = [float('inf')] * n
    distancias[inicio_idx] = 0.0
    previos = [-1] * n
    visitados = [False] * n
    
    # Cola de prioridad: (distancia, nodo)
    cola = [(0.0, inicio_idx)]
    
    while cola:
        dist_actual, nodo_actual = heapq.heappop(cola)
        
        if visitados[nodo_actual]:
            continue
        
        visitados[nodo_actual] = True
        
        # Si llegamos al destino, reconstruir el camino
        if nodo_actual == fin_idx:
            camino = []
            nodo = fin_idx
            while nodo != -1:
                camino.append(nodo)
                nodo = previos[nodo]
            camino.reverse()
            return distancias[fin_idx], camino
        
        # Explorar vecinos
        for vecino in range(n):
            if not visitados[vecino] and matriz_adyacencia[nodo_actual][vecino] != float('inf'):
                nueva_dist = dist_actual + matriz_adyacencia[nodo_actual][vecino]
                
                if nueva_dist < distancias[vecino]:
                    distancias[vecino] = nueva_dist
                    previos[vecino] = nodo_actual
                    heapq.heappush(cola, (nueva_dist, vecino))
    
    # No se encontró camino
    return float('inf'), []

