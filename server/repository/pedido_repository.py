from typing import List, Optional, Tuple
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
    
    def _obtener_nodos_por_zona(self, lat_centro: float, lon_centro: float, radio_km: float = 15.0, separacion_minima_km: float = 1.0) -> List[int]:
        """
        Obtiene nodos que están dentro de un radio específico desde un punto central,
        asegurando que estén separados entre sí por una distancia mínima.
        """
        from services.ruta_service import convertir_utm_a_latlon
        import math
        
        def distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            """Calcula distancia entre dos puntos en km"""
            R = 6371
            lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
            lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad
            a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c
        
        nodos_en_zona = []
        grafo = grafo_wrapper.graph
        
        for nodo_id in grafo.Vertices:
            coords_utm = grafo.get_node_coords(nodo_id)
            if coords_utm and coords_utm != (0, 0):
                lat, lon = convertir_utm_a_latlon(coords_utm[0], coords_utm[1])
                
                # Calcular distancia al centro
                distancia = distancia_haversine(lat_centro, lon_centro, lat, lon)
                
                if distancia <= radio_km:
                    nodos_en_zona.append((nodo_id, distancia, lat, lon))
        
        # Ordenar por distancia al centro
        nodos_en_zona.sort(key=lambda x: x[1])
        
        # Filtrar para asegurar separación mínima entre nodos seleccionados
        nodos_seleccionados = []
        for nodo_id, distancia, lat, lon in nodos_en_zona:
            # Verificar que esté suficientemente separado de los nodos ya seleccionados
            muy_cerca = False
            for nodo_sel_id, _, lat_sel, lon_sel in nodos_seleccionados:
                dist_entre_nodos = distancia_haversine(lat, lon, lat_sel, lon_sel)
                if dist_entre_nodos < separacion_minima_km:
                    muy_cerca = True
                    break
            
            if not muy_cerca:
                nodos_seleccionados.append((nodo_id, distancia, lat, lon))
        
        return [nodo[0] for nodo in nodos_seleccionados]
    
    def _inicializar_datos_mock(self):
        """Inicializa el repositorio con datos mock usando coordenadas hardcodeadas"""
        try:
            hoy = date.today()
            
            # COORDENADAS HARDCODEADAS - Cada pedido tiene coordenadas fijas que nunca cambian
            # IMPORTANTE: Tanto SAGA como RIPLEY deben tener pedidos BIEN ESPARCIDOS por toda Lima Metropolitana
            # SAGA (índices pares: 0, 2, 4, 6, 8, 10): 6 pedidos distribuidos
            # RIPLEY (índices impares: 1, 3, 5, 7, 9, 11): 6 pedidos distribuidos en DIFERENTES zonas
            # Coordenadas en formato (latitud, longitud)
            # Mínimo 12-15km entre cada pedido de la misma tienda
            coordenadas_saga = [
                (-12.0950, -77.0280),  # 0 - María González - San Isidro (CENTRO)
                (-12.2200, -76.9500),  # 2 - Ana Martínez - Villa El Salvador (SUR-ESTE - ~18km)
                (-11.9000, -77.1000),  # 4 - Carmen López - Comas (NORTE - ~22km)
                (-12.0500, -76.8000),  # 6 - Patricia Torres - Chaclacayo (ESTE - ~20km)
                (-12.2800, -77.0000),  # 8 - Sofía Herrera - Punta Hermosa (SUR - ~20km)
                (-11.8500, -77.0500),  # 10 - Laura Jiménez - Carabayllo (NORTE - ~25km)
            ]
            
            coordenadas_ripley = [
                (-12.0400, -77.1200),  # 1 - Carlos Rodríguez - Callao (OESTE - ~10km)
                (-12.1600, -77.0200),  # 3 - Luis Fernández - Barranco (SUR - ~8km)
                (-12.0700, -76.9200),  # 5 - Roberto Sánchez - La Molina (ESTE - ~12km)
                (-12.1100, -77.0500),  # 7 - Jorge Ramírez - San Borja (SUR - ~6km)
                (-11.9800, -77.0200),  # 9 - Miguel Vargas - Independencia (NORTE - ~12km)
                (-12.1800, -77.0800),  # 11 - Diego Morales - Chorrillos (SUR-OESTE - ~12km)
            ]
            
            # Datos hardcodeados de clientes - SAGA (6 pedidos)
            clientes_saga = [
                {"nombre": "María González", "direccion": "Av. Javier Prado 1234, San Isidro", "telefono": "987654321", "coords": coordenadas_saga[0], "tienda": "Saga"},
                {"nombre": "Ana Martínez", "direccion": "Av. Arequipa 890, Miraflores", "telefono": "987654323", "coords": coordenadas_saga[1], "tienda": "Saga"},
                {"nombre": "Carmen López", "direccion": "Av. La Marina 456, San Miguel", "telefono": "987654325", "coords": coordenadas_saga[2], "tienda": "Saga"},
                {"nombre": "Patricia Torres", "direccion": "Av. Angamos 321, Surco", "telefono": "987654327", "coords": coordenadas_saga[3], "tienda": "Saga"},
                {"nombre": "Sofía Herrera", "direccion": "Av. Túpac Amaru 987, Independencia", "telefono": "987654329", "coords": coordenadas_saga[4], "tienda": "Saga"},
                {"nombre": "Laura Jiménez", "direccion": "Av. Primavera 258, Chorrillos", "telefono": "987654331", "coords": coordenadas_saga[5], "tienda": "Saga"},
            ]
            
            # Datos hardcodeados de clientes - RIPLEY (6 pedidos diferentes)
            clientes_ripley = [
                {"nombre": "Carlos Rodríguez", "direccion": "Av. Guardia Civil 456, Callao", "telefono": "987654322", "coords": coordenadas_ripley[0], "tienda": "Ripley"},
                {"nombre": "Luis Fernández", "direccion": "Av. Grau 789, Barranco", "telefono": "987654324", "coords": coordenadas_ripley[1], "tienda": "Ripley"},
                {"nombre": "Roberto Sánchez", "direccion": "Av. La Molina 321, La Molina", "telefono": "987654326", "coords": coordenadas_ripley[2], "tienda": "Ripley"},
                {"nombre": "Jorge Ramírez", "direccion": "Av. San Borja Norte 654, San Borja", "telefono": "987654328", "coords": coordenadas_ripley[3], "tienda": "Ripley"},
                {"nombre": "Miguel Vargas", "direccion": "Av. Túpac Amaru 147, Independencia", "telefono": "987654330", "coords": coordenadas_ripley[4], "tienda": "Ripley"},
                {"nombre": "Diego Morales", "direccion": "Av. Defensores del Morro 369, Chorrillos", "telefono": "987654332", "coords": coordenadas_ripley[5], "tienda": "Ripley"},
            ]
            
            # Procesar SAGA y RIPLEY por separado con la misma lógica
            # Cada tienda debe tener nodos bien distribuidos por toda Lima
            nodos_seleccionados_saga = []
            nodos_seleccionados_ripley = []
            nodos_ya_usados = set()  # Para asegurar que cada nodo sea único (entre todas las tiendas)
            
            # Función auxiliar para procesar clientes de una tienda
            def procesar_clientes_tienda(clientes_tienda, nombre_tienda):
                """Procesa los clientes de una tienda y retorna los nodos seleccionados"""
                nodos_seleccionados = []
                coordenadas_nodos_usados = []  # Para verificar separación mínima dentro de esta tienda
                
                # Verificar que el grafo esté disponible
                if hasattr(grafo_wrapper, 'graph') and grafo_wrapper.graph is not None:
                    try:
                        nodos_reales = list(grafo_wrapper.graph.Vertices) if hasattr(grafo_wrapper.graph, 'Vertices') and grafo_wrapper.graph.Vertices else []
                        
                        # Obtener coordenadas de TODOS los nodos disponibles
                        nodos_con_coords = []
                        for nodo_id in nodos_reales:
                            try:
                                coords_utm = grafo_wrapper.graph.get_node_coords(nodo_id)
                                if coords_utm is not None and len(coords_utm) == 2:
                                    utm_x, utm_y = coords_utm[0], coords_utm[1]
                                    if utm_x != 0 or utm_y != 0:
                                        try:
                                            nodo_lat, nodo_lon = self._convertir_utm_a_latlon(utm_x, utm_y)
                                            if -13.0 < nodo_lat < -11.0 and -78.0 < nodo_lon < -76.0:
                                                nodos_con_coords.append((nodo_id, nodo_lat, nodo_lon))
                                        except Exception:
                                            pass
                            except Exception:
                                continue
                        
                        # Si no hay nodos con coordenadas válidas, usar distribución directa
                        if len(nodos_con_coords) == 0 and len(nodos_reales) > 0:
                            print(f"⚠️ [{nombre_tienda}] No se encontraron nodos con coordenadas válidas. Usando distribución directa...")
                            paso = max(1, len(nodos_reales) // len(clientes_tienda))
                            for i, cliente in enumerate(clientes_tienda):
                                indice_nodo = (i * paso) % len(nodos_reales)
                                nodo_id = nodos_reales[indice_nodo]
                                while nodo_id in nodos_ya_usados:
                                    indice_nodo = (indice_nodo + 1) % len(nodos_reales)
                                    nodo_id = nodos_reales[indice_nodo]
                                nodos_seleccionados.append(nodo_id)
                                nodos_ya_usados.add(nodo_id)
                                lat_obj, lon_obj = cliente["coords"]
                                coordenadas_nodos_usados.append((lat_obj, lon_obj))
                                print(f"✅ [{nombre_tienda}] Cliente {cliente['nombre']}: Nodo {nodo_id} (distribuido uniformemente)")
                        else:
                            # Buscar nodos distribuidos para cada cliente
                            separacion_minima_km = 8.0
                            
                            for cliente in clientes_tienda:
                                lat_objetivo, lon_objetivo = cliente["coords"]
                                nodo_seleccionado = None
                                mejor_distancia = float('inf')
                                
                                # Buscar nodos candidatos cerca de la coordenada objetivo
                                candidatos = []
                                for nodo_id, nodo_lat, nodo_lon in nodos_con_coords:
                                    if nodo_id in nodos_ya_usados:
                                        continue
                                    
                                    distancia_objetivo = self._distancia_haversine(lat_objetivo, lon_objetivo, nodo_lat, nodo_lon)
                                    if distancia_objetivo > 25.0:
                                        continue
                                    
                                    muy_cerca_de_otros = False
                                    for (lat_otro, lon_otro) in coordenadas_nodos_usados:
                                        distancia_entre_nodos = self._distancia_haversine(nodo_lat, nodo_lon, lat_otro, lon_otro)
                                        if distancia_entre_nodos < separacion_minima_km:
                                            muy_cerca_de_otros = True
                                            break
                                    
                                    if not muy_cerca_de_otros:
                                        candidatos.append((nodo_id, distancia_objetivo, nodo_lat, nodo_lon))
                                
                                candidatos.sort(key=lambda x: x[1])
                                
                                if candidatos:
                                    nodo_seleccionado, mejor_distancia, nodo_lat, nodo_lon = candidatos[0]
                                else:
                                    # Buscar cualquier nodo no usado y bien separado
                                    for nodo_id, nodo_lat, nodo_lon in nodos_con_coords:
                                        if nodo_id in nodos_ya_usados:
                                            continue
                                        
                                        muy_cerca = False
                                        for (lat_otro, lon_otro) in coordenadas_nodos_usados:
                                            distancia_entre = self._distancia_haversine(nodo_lat, nodo_lon, lat_otro, lon_otro)
                                            if distancia_entre < separacion_minima_km:
                                                muy_cerca = True
                                                break
                                        
                                        if not muy_cerca:
                                            nodo_seleccionado = nodo_id
                                            mejor_distancia = self._distancia_haversine(lat_objetivo, lon_objetivo, nodo_lat, nodo_lon)
                                            break
                                
                                if nodo_seleccionado is None:
                                    # Último recurso: cualquier nodo no usado
                                    for nodo_id in nodos_reales:
                                        if nodo_id not in nodos_ya_usados:
                                            nodo_seleccionado = nodo_id
                                            break
                                
                                if nodo_seleccionado is not None:
                                    try:
                                        coords_utm = grafo_wrapper.graph.get_node_coords(nodo_seleccionado)
                                        if coords_utm and coords_utm != (0, 0):
                                            nodo_lat_final, nodo_lon_final = self._convertir_utm_a_latlon(coords_utm[0], coords_utm[1])
                                        else:
                                            nodo_lat_final, nodo_lon_final = lat_objetivo, lon_objetivo
                                    except:
                                        nodo_lat_final, nodo_lon_final = lat_objetivo, lon_objetivo
                                    
                                    nodos_seleccionados.append(nodo_seleccionado)
                                    nodos_ya_usados.add(nodo_seleccionado)
                                    coordenadas_nodos_usados.append((nodo_lat_final, nodo_lon_final))
                                    print(f"✅ [{nombre_tienda}] Cliente {cliente['nombre']}: Nodo {nodo_seleccionado} en ({nodo_lat_final:.6f}, {nodo_lon_final:.6f})")
                                else:
                                    raise Exception(f"No se pudo encontrar nodo para {cliente['nombre']}")
                        
                        return nodos_seleccionados
                    
                    except Exception as e:
                        print(f"⚠️ ERROR [{nombre_tienda}]: {e}")
                        import traceback
                        traceback.print_exc()
                        # Fallback: usar nodos distribuidos
                        if len(nodos_reales) > 0:
                            paso = max(1, len(nodos_reales) // len(clientes_tienda))
                            nodos_fallback = []
                            for i, cliente in enumerate(clientes_tienda):
                                indice_nodo = (i * paso) % len(nodos_reales)
                                nodo_id = nodos_reales[indice_nodo]
                                while nodo_id in nodos_ya_usados:
                                    indice_nodo = (indice_nodo + 1) % len(nodos_reales)
                                    nodo_id = nodos_reales[indice_nodo]
                                nodos_fallback.append(nodo_id)
                                nodos_ya_usados.add(nodo_id)
                            return nodos_fallback
                        return []
                else:
                    raise Exception("El grafo no está disponible")
            
            # Procesar SAGA primero
            print(f"\n🏪 Procesando pedidos de SAGA...")
            nodos_seleccionados_saga = procesar_clientes_tienda(clientes_saga, "SAGA")
            
            # Procesar RIPLEY después
            print(f"\n🏪 Procesando pedidos de RIPLEY...")
            nodos_seleccionados_ripley = procesar_clientes_tienda(clientes_ripley, "RIPLEY")
            
            # Combinar todos los nodos seleccionados (Saga primero, luego Ripley)
            nodos_seleccionados = nodos_seleccionados_saga + nodos_seleccionados_ripley
            
            # Combinar todos los clientes (Saga primero, luego Ripley)
            clientes_data = clientes_saga + clientes_ripley
            
            print(f"\n📊 Resumen:")
            print(f"   SAGA: {len(nodos_seleccionados_saga)} nodos seleccionados")
            print(f"   RIPLEY: {len(nodos_seleccionados_ripley)} nodos seleccionados")
            print(f"   Total: {len(nodos_seleccionados)} nodos únicos")
            
            # Crear pedidos mock con información de clientes
            pedidos_mock = []
            for i, cliente in enumerate(clientes_data):
                if i < len(nodos_seleccionados):
                    # Usar la tienda asignada en los datos del cliente (ya viene en el diccionario)
                    tienda = cliente.get("tienda", "Saga" if i < 6 else "Ripley")  # Los primeros 6 son Saga, los siguientes 6 son Ripley
                    # Fechas variadas pero determinísticas (basadas en el índice)
                    dias_atras = i % 6  # 0 a 5 días, pero siempre el mismo para cada cliente
                    
                    pedidos_mock.append(PedidoCreate(
                        tienda=tienda,
                        fecha=hoy - timedelta(days=dias_atras),
                        nodo_destino=nodos_seleccionados[i],
                        cliente_nombre=cliente["nombre"],
                        cliente_direccion=cliente["direccion"],
                        cliente_telefono=cliente["telefono"]
                    ))
            
            # Crear los pedidos
            for i, pedido_data in enumerate(pedidos_mock):
                try:
                    self.create(pedido_data)
                    lat, lon = clientes_data[i]["coords"]
                    print(f"✅ Pedido creado: {pedido_data.cliente_nombre} - Nodo: {pedido_data.nodo_destino} - Coordenadas fijas: ({lat:.6f}, {lon:.6f})")
                except Exception as e:
                    print(f"❌ ERROR al crear pedido para {pedido_data.cliente_nombre}: {e}")
            
            print(f"✅ Inicialización completada: {len(pedidos_mock)} pedidos creados exitosamente con coordenadas hardcodeadas")
        
        except Exception as e:
            print(f"❌ ERROR CRÍTICO en _inicializar_datos_mock: {e}")
            import traceback
            traceback.print_exc()
            print("⚠️ Continuando sin datos mock. El servidor funcionará pero sin pedidos iniciales.")
    
    def create(self, pedido_data: PedidoCreate) -> Pedido:
        """Crea un nuevo pedido"""
        pedido = Pedido(
            id=self._next_id,
            tienda=pedido_data.tienda,
            fecha=pedido_data.fecha,
            nodo_destino=pedido_data.nodo_destino,
            cliente_nombre=pedido_data.cliente_nombre,
            cliente_direccion=pedido_data.cliente_direccion,
            cliente_telefono=pedido_data.cliente_telefono,
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

