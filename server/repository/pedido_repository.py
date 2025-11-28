from typing import List, Optional
from datetime import date, timedelta
import random
import sys
import os
import heapq
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models.pedido import Pedido, PedidoCreate, PedidoUpdate
from models.grafo_wrapper import grafo_wrapper

class PedidoRepository:
    """Repository pattern para gestionar pedidos en memoria"""
    
    def __init__(self):
        self._pedidos: dict[int, Pedido] = {}
        self._next_id = 1
        self._inicializar_datos_mock()
    
    def _verificar_camino_entre_nodos(self, origen: int, destino: int, max_intentos: int = 1000) -> bool:
        """
        Verifica si existe un camino entre dos nodos usando BFS simplificado.
        
        Args:
            origen: ID del nodo origen
            destino: ID del nodo destino
            max_intentos: Máximo número de nodos a explorar
        
        Returns:
            True si existe un camino, False en caso contrario
        """
        if origen not in grafo_wrapper.graph.label2v or destino not in grafo_wrapper.graph.label2v:
            return False
        
        if origen == destino:
            return True
        
        visitados = set()
        cola = [origen]
        visitados.add(origen)
        intentos = 0
        
        while cola and intentos < max_intentos:
            intentos += 1
            nodo_actual = cola.pop(0)
            
            if nodo_actual == destino:
                return True
            
            # Obtener vecinos
            vecinos = grafo_wrapper.graph.get_children(nodo_actual)
            padres = grafo_wrapper.graph.get_parents(nodo_actual)
            todos_vecinos = set(vecinos + padres)
            
            for vecino in todos_vecinos:
                if vecino not in visitados:
                    visitados.add(vecino)
                    cola.append(vecino)
        
        return False
    
    def _obtener_nodos_reales(self, cantidad: int) -> List[int]:
        """
        Obtiene una lista aleatoria de nodos reales del árbol/grafo.
        Asegura que el origen (primer nodo) y destino (segundo nodo) tengan un camino válido.
        
        Args:
            cantidad: Número de nodos a seleccionar (mínimo 2)
        
        Returns:
            Lista de IDs de nodos del grafo, donde los primeros 2 tienen camino válido
        """
        try:
            nodos_disponibles = list(grafo_wrapper.graph.Vertices)
            if len(nodos_disponibles) == 0:
                print("⚠️ ADVERTENCIA PedidoRepository: No hay nodos disponibles en el grafo")
                return []
            
            # Asegurar que siempre haya al menos 2 nodos
            cantidad = max(2, cantidad)
            cantidad = min(cantidad, len(nodos_disponibles))
            
            # Seleccionar origen y destino que tengan camino válido
            max_intentos_busqueda = 50  # Intentar hasta 50 veces encontrar un par válido
            intentos = 0
            
            while intentos < max_intentos_busqueda:
                intentos += 1
                
                # Seleccionar origen y destino aleatorios
                origen, destino = random.sample(nodos_disponibles, 2)
                
                # Verificar que existe camino entre origen y destino
                if self._verificar_camino_entre_nodos(origen, destino):
                    # Si hay camino, seleccionar el resto de nodos aleatoriamente
                    nodos_restantes = [n for n in nodos_disponibles if n != origen and n != destino]
                    
                    if cantidad == 2:
                        nodos_seleccionados = [origen, destino]
                    else:
                        # Seleccionar nodos adicionales aleatoriamente
                        cantidad_adicional = cantidad - 2
                        nodos_adicionales = random.sample(nodos_restantes, min(cantidad_adicional, len(nodos_restantes)))
                        nodos_seleccionados = [origen, destino] + nodos_adicionales
                    
                    print(f"✅ PedidoRepository: Seleccionados {len(nodos_seleccionados)} nodos con camino válido")
                    print(f"   Origen: {origen}, Destino: {destino}")
                    print(f"   Nodos completos: {nodos_seleccionados}")
                    print(f"   Total de nodos disponibles en grafo: {len(nodos_disponibles)}")
                    return nodos_seleccionados
            
            # Si después de varios intentos no se encontró un par válido, usar selección aleatoria simple
            print(f"⚠️ ADVERTENCIA: No se encontró par con camino válido después de {max_intentos_busqueda} intentos")
            print(f"   Usando selección aleatoria simple (puede fallar al calcular ruta)")
            nodos_seleccionados = random.sample(nodos_disponibles, cantidad)
            return nodos_seleccionados
            
        except Exception as e:
            print(f"❌ ERROR al obtener nodos del grafo: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _inicializar_datos_mock(self):
        """Inicializa el repositorio con datos mock usando nodos reales del grafo"""
        hoy = date.today()
        
        # Obtener nodos reales del grafo
        nodos_reales = list(grafo_wrapper.graph.Vertices) if grafo_wrapper.graph.Vertices else []
        
        if len(nodos_reales) == 0:
            print("Advertencia: No hay nodos disponibles en el grafo. Los pedidos mock no se crearán.")
            return
        
        # Crear pedidos mock con 2 o más nodos del árbol para poder calcular rutas con TSP
        pedidos_mock = [
            PedidoCreate(
                tienda="Saga",
                fecha=hoy - timedelta(days=3),
                nodos=self._obtener_nodos_reales(random.randint(3, 6))  # Entre 3 y 6 nodos
            ),
            PedidoCreate(
                tienda="Ripley",
                fecha=hoy - timedelta(days=3),
                nodos=self._obtener_nodos_reales(random.randint(2, 5))  # Entre 2 y 5 nodos
            ),
            PedidoCreate(
                tienda="Saga",
                fecha=hoy - timedelta(days=2),
                nodos=self._obtener_nodos_reales(random.randint(4, 7))  # Entre 4 y 7 nodos
            ),
            PedidoCreate(
                tienda="Ripley",
                fecha=hoy - timedelta(days=2),
                nodos=self._obtener_nodos_reales(random.randint(2, 4))  # Entre 2 y 4 nodos
            ),
            PedidoCreate(
                tienda="Saga",
                fecha=hoy - timedelta(days=1),
                nodos=self._obtener_nodos_reales(random.randint(3, 5))  # Entre 3 y 5 nodos
            ),
            PedidoCreate(
                tienda="Ripley",
                fecha=hoy - timedelta(days=1),
                nodos=self._obtener_nodos_reales(random.randint(2, 6))  # Entre 2 y 6 nodos
            ),
            PedidoCreate(
                tienda="Saga",
                fecha=hoy,
                nodos=self._obtener_nodos_reales(random.randint(2, 4))  # Entre 2 y 4 nodos
            ),
            PedidoCreate(
                tienda="Ripley",
                fecha=hoy,
                nodos=self._obtener_nodos_reales(random.randint(3, 6))  # Entre 3 y 6 nodos
            ),
        ]
        
        # Crear los pedidos mock solo si tienen al menos 2 nodos (necesario para TSP)
        for pedido_data in pedidos_mock:
            if len(pedido_data.nodos) >= 2:
                self.create(pedido_data)
                print(f"Pedido creado con {len(pedido_data.nodos)} nodos: {pedido_data.nodos[:5]}...")  # Mostrar primeros 5
            else:
                print(f"Advertencia: Pedido no creado porque tiene menos de 2 nodos: {len(pedido_data.nodos)}")
    
    def create(self, pedido_data: PedidoCreate) -> Pedido:
        """Crea un nuevo pedido"""
        pedido = Pedido(
            id=self._next_id,
            tienda=pedido_data.tienda,
            fecha=pedido_data.fecha,
            nodos=pedido_data.nodos,
            ruta_optimizada=None
        )
        self._pedidos[self._next_id] = pedido
        self._next_id += 1
        return pedido
    
    def get_by_id(self, pedido_id: int) -> Optional[Pedido]:
        """Obtiene un pedido por su ID"""
        return self._pedidos.get(pedido_id)
    
    def get_all(self, tienda: Optional[str] = None) -> List[Pedido]:
        """Obtiene todos los pedidos, opcionalmente filtrados por tienda"""
        pedidos = list(self._pedidos.values())
        if tienda:
            pedidos = [p for p in pedidos if p.tienda.lower() == tienda.lower()]
        return pedidos
    
    def update(self, pedido_id: int, pedido_data: PedidoUpdate) -> Optional[Pedido]:
        """Actualiza un pedido existente"""
        if pedido_id not in self._pedidos:
            return None
        
        pedido = self._pedidos[pedido_id]
        update_data = pedido_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(pedido, field, value)
        
        return pedido
    
    def delete(self, pedido_id: int) -> bool:
        """Elimina un pedido"""
        if pedido_id in self._pedidos:
            del self._pedidos[pedido_id]
            return True
        return False
    
    def update_ruta_optimizada(self, pedido_id: int, ruta: List[int]) -> Optional[Pedido]:
        """Actualiza la ruta optimizada de un pedido"""
        if pedido_id not in self._pedidos:
            return None
        
        self._pedidos[pedido_id].ruta_optimizada = ruta
        return self._pedidos[pedido_id]

