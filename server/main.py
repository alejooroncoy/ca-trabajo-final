import matplotlib.pyplot as plt
import csv
import math

class Graph:
    """Representa un grafo para modelar el sistema vial de Lima"""
    def __init__(self):
        self.Vertices = []  # Lista de todos los nodos del grafo
        self.label2v = dict()  # Mapeo de etiquetas a índices de vértices
        self.G = []  # Lista de adyacencia para representar las conexiones
        self.coordenadas = {}  # Guarda la posición geográfica de cada nodo
        self.lineas_nodo = {}  # Registra qué líneas de transporte pasan por cada nodo

    def node(self, label, x=None, y=None, lineas=None):
        """Crea un nuevo nodo en el grafo con su ubicación y líneas de transporte"""
        self.label2v[label] = len(self.Vertices)  # Asigna un índice único al nodo
        self.Vertices.append(label)  # Agrega el nodo a la lista principal
        self.G.append([])  # Inicializa la lista de conexiones vacía
        if x is not None and y is not None:
            self.coordenadas[label] = (x, y)  # Guarda la posición geográfica
        if lineas is not None:
            self.lineas_nodo[label] = lineas  # Registra las líneas que pasan por aquí

    def nodes(self, labels):
        """Crea varios nodos de una vez para mayor eficiencia"""
        for label in labels:
            self.node(label)

    def edge(self, u, v):
        """Conecta dos nodos creando una arista entre ellos"""
        u = self.label2v[u]  # Convierte la etiqueta a índice
        v = self.label2v[v]  # Convierte la etiqueta a índice
        self.G[u].append(v)  # Agrega la conexión en la lista de adyacencia

    def edges(self, u, vs):
        """Conecta un nodo con varios otros nodos de una vez"""
        for v in vs:
            self.edge(u, v)
    
    def get_node_coords(self, label):
        """Devuelve la posición geográfica (latitud, longitud) de un nodo"""
        return self.coordenadas.get(label, (0, 0))  # Retorna (0,0) si no existe
    
    def get_node_lineas(self, label):
        """Devuelve todas las líneas de transporte que pasan por este nodo"""
        return self.lineas_nodo.get(label, set())  # Retorna conjunto vacío si no hay líneas
    
    def get_children(self, label):
        """Encuentra todos los nodos conectados directamente desde este nodo"""
        if label not in self.label2v:
            return []  # El nodo no existe
        u = self.label2v[label]  # Obtiene el índice del nodo
        return [self.Vertices[v] for v in self.G[u]]  # Convierte índices a etiquetas
    
    def get_parents(self, label):
        """Encuentra todos los nodos que tienen conexión directa hacia este nodo"""
        if label not in self.label2v:
            return []  # El nodo no existe
        v = self.label2v[label]  # Obtiene el índice del nodo
        parents = []
        # Busca en todas las listas de adyacencia
        for u in range(len(self.G)):
            if v in self.G[u]:  # Si encuentra este nodo como destino
                parents.append(self.Vertices[u])  # Agrega el nodo origen
        return parents
    
    def is_leaf(self, label):
        """Determina si un nodo es terminal (no tiene conexiones salientes)"""
        return len(self.get_children(label)) == 0
    
    def is_root(self, label):
        """Determina si un nodo es el punto de partida (no tiene conexiones entrantes)"""
        return len(self.get_parents(label)) == 0
    
    def get_all_nodes(self):
        """Devuelve una copia de todos los nodos del grafo"""
        return self.Vertices.copy()
    
    def get_edges(self):
        """Extrae todas las conexiones del grafo como pares de nodos"""
        edges = []
        for u in range(len(self.G)):  # Para cada nodo origen
            for v in self.G[u]:  # Para cada nodo destino conectado
                edges.append((self.Vertices[u], self.Vertices[v]))  # Guarda la conexión
        return edges

class ArbolVialLima:
    """Gestiona la representación en árbol del sistema de transporte de Lima"""
    
    def __init__(self):
        self.graph = Graph()  # Estructura de datos para el grafo
        self.lineas_viales = []  # Lista de todas las rutas de transporte
        self.aristas = []  # Conexiones entre nodos con sus pesos
        self.raiz = None  # Nodo principal del árbol (el más conectado)
    
    def cargar_datos_csv(self, archivo_csv):
        """Lee el archivo CSV y construye la red de nodos del sistema vial"""
        print("Cargando datos del sistema vial...")
        
        with open(archivo_csv, 'r', encoding='utf-8') as archivo:
            lector = csv.DictReader(archivo)
            
            for fila in lector:
                try:
                    # Extrae las coordenadas de inicio y fin de cada ruta
                    x_inicio = float(fila['longitud'])
                    y_inicio = float(fila['latitud'])
                    x_fin = float(fila['longitud_final'])
                    y_fin = float(fila['latitud_final'])
                    id_linea = int(fila['id'])
                    
                    # Crea o encuentra nodos para los puntos de inicio y fin
                    nodo_inicio = self._crear_o_obtener_nodo(x_inicio, y_inicio, id_linea)
                    nodo_fin = self._crear_o_obtener_nodo(x_fin, y_fin, id_linea)
                    
                    # Registra esta ruta en nuestro sistema
                    self.lineas_viales.append({
                        'id': id_linea,
                        'inicio': nodo_inicio,
                        'fin': nodo_fin
                    })
                    
                except (ValueError, KeyError):
                    continue  # Ignora filas con datos inválidos
        
        print(f"Procesados {len(self.graph.Vertices)} nodos y {len(self.lineas_viales)} rutas")
    
    def _crear_o_obtener_nodo(self, x, y, id_linea):
        """Encuentra un nodo cercano existente o crea uno nuevo si no hay ninguno cerca"""
        # Busca si ya existe un nodo muy cerca de estas coordenadas
        for label in self.graph.Vertices:
            nx, ny = self.graph.get_node_coords(label)
            distancia = math.sqrt((x - nx)**2 + (y - ny)**2)
            if distancia < 10:  # Si está a menos de 10 unidades de distancia
                # Actualiza las líneas que pasan por este nodo existente
                lineas_actuales = self.graph.get_node_lineas(label)
                lineas_actuales.add(id_linea)
                self.graph.lineas_nodo[label] = lineas_actuales
                return label  # Retorna el nodo existente
        
        # Si no hay nodos cercanos, crea uno nuevo
        nodo_id = len(self.graph.Vertices)  # Usa el número de nodos como ID
        self.graph.node(nodo_id, x, y, {id_linea})  # Crea el nodo con esta línea
        return nodo_id
    
    def construir_arbol(self):
        """Organiza los nodos en una estructura de árbol jerárquica"""
        print("Construyendo estructura de árbol...")
        
        # Primero identifica todas las conexiones posibles entre nodos
        self._detectar_conexiones()
        
        # Elige como raíz al nodo con más líneas de transporte (más importante)
        nodo_raiz_id = max(self.graph.Vertices, 
                          key=lambda label: len(self.graph.get_node_lineas(label)))
        self.raiz = nodo_raiz_id
        
        # Construye el árbol usando búsqueda en amplitud desde la raíz
        self._construir_arbol_bfs()
        
        print(f"Árbol completado - Nodo central: {nodo_raiz_id}")
    
    def _detectar_conexiones(self):
        """Identifica todas las conexiones posibles entre nodos del sistema"""
        # Conecta nodos que comparten líneas de transporte (conexiones directas)
        for linea in self.lineas_viales:
            nodo_inicio = linea['inicio']
            nodo_fin = linea['fin']
            
            if nodo_inicio != nodo_fin:  # Evita auto-conexiones
                lineas_inicio = self.graph.get_node_lineas(nodo_inicio)
                lineas_fin = self.graph.get_node_lineas(nodo_fin)
                peso = len(lineas_inicio.intersection(lineas_fin))  # Líneas compartidas
                if peso > 0:
                    self.aristas.append((nodo_inicio, nodo_fin, peso))
        
        # Conecta nodos cercanos geográficamente (conexiones por proximidad)
        nodos_lista = self.graph.Vertices
        for i, nodo1 in enumerate(nodos_lista):
            x1, y1 = self.graph.get_node_coords(nodo1)
            lineas1 = self.graph.get_node_lineas(nodo1)
            
            for j, nodo2 in enumerate(nodos_lista[i+1:], i+1):
                x2, y2 = self.graph.get_node_coords(nodo2)
                lineas2 = self.graph.get_node_lineas(nodo2)
                
                distancia = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                
                # Si están cerca pero no comparten líneas, los conecta
                if distancia < 50 and not lineas1.intersection(lineas2):
                    peso = max(1, int(100 / distancia))  # Peso inverso a la distancia
                    self.aristas.append((nodo1, nodo2, peso))
        
        print(f"Identificadas {len(self.aristas)} conexiones entre nodos")
    
    def _construir_arbol_bfs(self):
        """Construye la estructura de árbol usando búsqueda en amplitud desde la raíz"""
        # Primero, crear TODAS las conexiones bidireccionales basadas en las aristas
        # Esto asegura que el grafo sea completamente conectado para pathfinding
        for nodo1, nodo2, peso in self.aristas:
            # Crear conexión bidireccional
            self.graph.edge(nodo1, nodo2)
            self.graph.edge(nodo2, nodo1)
        
        print(f"Conexiones bidireccionales creadas: {len(self.aristas) * 2} aristas")
        
        # Luego, construir el árbol usando BFS desde la raíz (para estructura jerárquica)
        visitados = set()  # Nodos ya procesados
        cola = [self.raiz]  # Cola para procesar nodos nivel por nivel
        visitados.add(self.raiz)
        
        while cola:
            nodo_actual = cola.pop(0)  # Toma el siguiente nodo de la cola
            
            # Busca nodos conectados que aún no han sido visitados
            for nodo1, nodo2, peso in self.aristas:
                nodo_conectado = None
                
                # Determina cuál nodo está conectado al actual
                if nodo1 == nodo_actual and nodo2 not in visitados:
                    nodo_conectado = nodo2
                elif nodo2 == nodo_actual and nodo1 not in visitados:
                    nodo_conectado = nodo1
                
                if nodo_conectado:
                    # Las conexiones ya están creadas arriba, solo marcamos como visitado
                    visitados.add(nodo_conectado)  # Marca como visitado
                    cola.append(nodo_conectado)  # Lo agrega para procesar después
    
    def generar_visualizacion(self, archivo_salida="lima_vial_geografico_completo.png"):
        """Crea una imagen visual del sistema vial de Lima con colores y tamaños representativos"""
        print("Generando visualización del sistema vial...")
        
        fig, ax = plt.subplots(1, 1, figsize=(20, 16))
        ax.set_facecolor('white')
        
        # Extrae todas las coordenadas para normalizar la visualización
        x_coords = [self.graph.get_node_coords(label)[0] for label in self.graph.Vertices]
        y_coords = [self.graph.get_node_coords(label)[1] for label in self.graph.Vertices]
        
        # Calcula los límites del mapa
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        # Normaliza las coordenadas para que quepan bien en la imagen
        x_norm = [(x - x_min) / (x_max - x_min) * 18 - 9 for x in x_coords]
        y_norm = [(y - y_min) / (y_max - y_min) * 14 - 7 for y in y_coords]
        
        # Dibuja las conexiones entre nodos con colores según su importancia
        for nodo1, nodo2, peso in self.aristas:
            idx1 = self.graph.Vertices.index(nodo1)
            idx2 = self.graph.Vertices.index(nodo2)
            x1, y1 = x_norm[idx1], y_norm[idx1]
            x2, y2 = x_norm[idx2], y_norm[idx2]
            
            # Asigna colores y grosor según la importancia de la conexión
            if peso > 3:  # Conexiones muy importantes
                color, alpha, width = '#FF6B6B', 0.8, 2.0  # Rojo fuerte
            elif peso > 1:  # Conexiones importantes
                color, alpha, width = '#4ECDC4', 0.6, 1.5  # Turquesa
            else:  # Conexiones menores
                color, alpha, width = '#45B7D1', 0.4, 1.0  # Azul claro
            
            ax.plot([x1, x2], [y1, y2], color=color, alpha=alpha, 
                    linewidth=width, zorder=1)
        
        # Dibuja los nodos con tamaños según su importancia
        for i, label in enumerate(self.graph.Vertices):
            x_norm_val, y_norm_val = x_norm[i], y_norm[i]
            
            num_conexiones = len(self.graph.get_node_lineas(label))
            # Asigna tamaño y color según el número de líneas que pasan por el nodo
            if num_conexiones > 5:  # Nodos muy importantes
                size, color = 80, '#E74C3C'  # Rojo - estaciones principales
            elif num_conexiones > 2:  # Nodos importantes
                size, color = 50, '#F39C12'  # Naranja - estaciones secundarias
            else:  # Nodos menores
                size, color = 30, '#3498DB'  # Azul - paradas simples
            
            ax.scatter(x_norm_val, y_norm_val, s=size, c=color, alpha=0.8, 
                      edgecolors='white', linewidth=1, zorder=2)
        
        # Configura los límites y aspecto de la visualización
        ax.set_xlim(-10, 10)
        ax.set_ylim(-8, 8)
        ax.set_aspect('equal')  # Mantiene proporciones correctas
        ax.axis('off')  # Oculta los ejes para una vista más limpia
        
        # Agrega título principal y estadísticas del sistema
        ax.text(0, -7.5, 'Sistema Vial Metropolitano de Lima - Red de Nodos Viales', 
                fontsize=16, ha='center', weight='bold', color='#2C3E50')
        
        ax.text(0, -8, f'Nodos: {len(self.graph.Vertices)} | Conexiones: {len(self.aristas)} | Rutas: {len(self.lineas_viales)}', 
                fontsize=12, ha='center', color='#7F8C8D')
        
        # Guarda la imagen en alta resolución
        plt.tight_layout()
        plt.savefig(archivo_salida, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        print(f"Imagen guardada como: {archivo_salida}")
    
    def mostrar_estadisticas_arbol(self):
        """Presenta un resumen detallado de la estructura del sistema vial"""
        print("\n=== ESTADÍSTICAS DEL SISTEMA VIAL ===")
        
        # Calcula estadísticas generales de la red
        total_nodos = len(self.graph.Vertices)
        nodos_hoja = sum(1 for label in self.graph.Vertices if self.graph.is_leaf(label))
        nodos_internos = total_nodos - nodos_hoja
        
        print(f"Total de nodos: {total_nodos} | Terminales: {nodos_hoja} | Intermedios: {nodos_internos}")
        print(f"Total de conexiones: {len(self.aristas)}")
        
        # Identifica los nodos más importantes del sistema
        nodos_ordenados = sorted(self.graph.Vertices, 
                               key=lambda label: len(self.graph.get_node_lineas(label)), reverse=True)
        
        print("\nTop 5 estaciones más importantes:")
        for i, label in enumerate(nodos_ordenados[:5]):
            lineas = len(self.graph.get_node_lineas(label))
            print(f"{i+1}. Estación {label}: {lineas} líneas de transporte")
        
        # Información sobre el nodo central del sistema
        hijos_raiz = self.graph.get_children(self.raiz)
        print(f"\nNodo central: {self.raiz} | Conexiones directas: {len(hijos_raiz)}")

def main():
    """Función principal que ejecuta todo el proceso de análisis del sistema vial"""
    # Inicializa el sistema de análisis
    arbol = ArbolVialLima()
    
    # Carga los datos del archivo CSV con las rutas del sistema
    arbol.cargar_datos_csv("Sistema_Vial_Metropolitano_A74.csv")
    
    # Construye la estructura jerárquica del sistema
    arbol.construir_arbol()
    
    # Genera la visualización gráfica del sistema
    arbol.generar_visualizacion()
    
    # Muestra estadísticas detalladas del sistema
    arbol.mostrar_estadisticas_arbol()
    
    print("\n¡Análisis del sistema vial completado exitosamente!")

if __name__ == "__main__":
    main()
