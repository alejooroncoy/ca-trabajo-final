import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from main import ArbolVialLima

class GrafoWrapper:
    """Wrapper para exponer el grafo a través de la API"""
    
    _instance = None
    _arbol = None
    
    def __init__(self):
        if GrafoWrapper._instance is None:
            GrafoWrapper._instance = self
            self._cargar_grafo()
    
    def _cargar_grafo(self):
        """Carga el grafo desde el CSV"""
        if GrafoWrapper._arbol is None:
            # Buscar el CSV en el directorio del servidor
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            csv_path = os.path.join(base_dir, "Sistema_Vial_Metropolitano_A74.csv")
            if not os.path.exists(csv_path):
                # Intentar ruta relativa desde models
                csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Sistema_Vial_Metropolitano_A74.csv")
            GrafoWrapper._arbol = ArbolVialLima()
            GrafoWrapper._arbol.cargar_datos_csv(csv_path)
            GrafoWrapper._arbol.construir_arbol()
    
    @property
    def arbol(self) -> ArbolVialLima:
        """Obtiene la instancia del árbol vial"""
        return GrafoWrapper._arbol
    
    @property
    def graph(self):
        """Obtiene el grafo"""
        return GrafoWrapper._arbol.graph
    
    @property
    def aristas(self):
        """Obtiene las aristas con pesos"""
        return GrafoWrapper._arbol.aristas
    
    def get_matriz_adyacencia(self):
        """Construye una matriz de adyacencia con pesos para los algoritmos"""
        nodos = self.graph.Vertices
        n = len(nodos)
        # Inicializar con infinito
        matriz = [[float('inf')] * n for _ in range(n)]
        
        # Crear diccionario de nodo a índice
        nodo_to_idx = {nodo: i for i, nodo in enumerate(nodos)}
        
        # Llenar con los pesos de las aristas
        for origen, destino, peso in self.aristas:
            if origen in nodo_to_idx and destino in nodo_to_idx:
                i = nodo_to_idx[origen]
                j = nodo_to_idx[destino]
                # El peso es inverso a la distancia, así que usamos 1/peso como distancia
                distancia = 1.0 / peso if peso > 0 else float('inf')
                matriz[i][j] = distancia
                matriz[j][i] = distancia  # Grafo no dirigido
        
        # Diagonal en 0
        for i in range(n):
            matriz[i][i] = 0.0
        
        return matriz, nodo_to_idx

# Instancia global
grafo_wrapper = GrafoWrapper()

