from typing import List, Tuple, Dict

def floyd_warshall(matriz_adyacencia: List[List[float]]) -> Tuple[List[List[float]], List[List[int]]]:
    """
    Algoritmo de Floyd-Warshall para encontrar los caminos más cortos entre todos los pares de nodos.
    
    Args:
        matriz_adyacencia: Matriz de adyacencia con pesos
    
    Returns:
        Tupla (matriz_distancias, matriz_predecesores)
        - matriz_distancias: Matriz con las distancias mínimas entre todos los pares
        - matriz_predecesores: Matriz para reconstruir los caminos
    """
    n = len(matriz_adyacencia)
    
    # Inicializar matrices de distancias y predecesores
    distancias = [[float('inf')] * n for _ in range(n)]
    predecesores = [[-1] * n for _ in range(n)]
    
    # Copiar la matriz de adyacencia inicial
    for i in range(n):
        for j in range(n):
            distancias[i][j] = matriz_adyacencia[i][j]
            if i != j and matriz_adyacencia[i][j] != float('inf'):
                predecesores[i][j] = i
    
    # Diagonal en 0 (distancia de un nodo a sí mismo)
    for i in range(n):
        distancias[i][i] = 0.0
        predecesores[i][i] = i
    
    # Floyd-Warshall: probar todos los nodos como intermediarios
    for k in range(n):
        for i in range(n):
            for j in range(n):
                # Si el camino a través de k es más corto
                if distancias[i][k] + distancias[k][j] < distancias[i][j]:
                    distancias[i][j] = distancias[i][k] + distancias[k][j]
                    predecesores[i][j] = predecesores[k][j]
    
    return distancias, predecesores

def reconstruir_camino_floyd_warshall(
    inicio_idx: int, 
    fin_idx: int, 
    predecesores: List[List[int]]
) -> List[int]:
    """
    Reconstruye el camino más corto entre dos nodos usando la matriz de predecesores.
    
    Args:
        inicio_idx: Índice del nodo inicial
        fin_idx: Índice del nodo destino
        predecesores: Matriz de predecesores del algoritmo Floyd-Warshall
    
    Returns:
        Lista de índices representando el camino (vacía si no hay camino)
    """
    # Verificar si existe un camino
    if predecesores[inicio_idx][fin_idx] == -1:
        return []
    
    # Reconstruir el camino desde el final hacia el inicio
    camino = []
    actual = fin_idx
    
    while actual != inicio_idx:
        camino.append(actual)
        actual = predecesores[inicio_idx][actual]
        
        # Evitar bucles infinitos
        if len(camino) > len(predecesores):
            return []
    
    camino.append(inicio_idx)
    camino.reverse()
    
    return camino

def encontrar_camino_floyd_warshall(
    matriz_adyacencia: List[List[float]], 
    inicio_idx: int, 
    fin_idx: int
) -> Tuple[float, List[int]]:
    """
    Encuentra el camino más corto entre dos nodos usando Floyd-Warshall.
    
    Args:
        matriz_adyacencia: Matriz de adyacencia con pesos
        inicio_idx: Índice del nodo inicial
        fin_idx: Índice del nodo destino
    
    Returns:
        Tupla (distancia_total, camino) donde camino es lista de índices
    """
    # Ejecutar Floyd-Warshall
    distancias, predecesores = floyd_warshall(matriz_adyacencia)
    
    # Obtener la distancia mínima
    distancia_total = distancias[inicio_idx][fin_idx]
    
    # Si no hay camino
    if distancia_total == float('inf'):
        return float('inf'), []
    
    # Reconstruir el camino
    camino = reconstruir_camino_floyd_warshall(inicio_idx, fin_idx, predecesores)
    
    return distancia_total, camino