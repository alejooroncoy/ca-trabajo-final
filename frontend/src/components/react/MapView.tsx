import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import '../../styles/map.css';
import { getNodos, getAristas, type Nodo, type Ruta, type Origen } from '../../services/api';

// Fix para iconos de Leaflet (usando URLs públicas)
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Constantes
const DEFAULT_VIEW: [number, number] = [-12.0464, -77.0428];
const DEFAULT_ZOOM = 10;
const MAX_ZOOM = 15;
const PADDING = [50, 50] as [number, number];

// Funciones helper
const isValidCoordinate = (lat: number, lng: number): boolean => {
  return !isNaN(lat) && !isNaN(lng) &&
         lat >= -90 && lat <= 90 &&
         lng >= -180 && lng <= 180;
};

const calculateDistance = (p1: [number, number], p2: [number, number]): number => {
  return Math.sqrt(Math.pow(p1[0] - p2[0], 2) + Math.pow(p1[1] - p2[1], 2));
};

const parseCoordinates = (coords: any[]): [number, number][] => {
  return coords
    .map((coord: any) => {
      if (Array.isArray(coord) && coord.length >= 2) {
        return [Number(coord[0]), Number(coord[1])] as [number, number];
      }
      return null;
    })
    .filter((coord: [number, number] | null): coord is [number, number] => coord !== null);
};

const adjustMapBounds = (map: L.Map, layers: L.Layer[], padding: number = 0.15) => {
  if (layers.length === 0) {
    map.setView(DEFAULT_VIEW, DEFAULT_ZOOM);
    return;
  }

  try {
    const group = L.featureGroup(layers);
    const bounds = group.getBounds();
    
    if (bounds.isValid()) {
      map.fitBounds(bounds.pad(padding), {
        padding: PADDING,
        maxZoom: MAX_ZOOM,
      });
    } else {
      map.setView(DEFAULT_VIEW, DEFAULT_ZOOM);
    }
  } catch (err) {
    console.error('Error al ajustar bounds:', err);
    map.setView(DEFAULT_VIEW, DEFAULT_ZOOM);
  }
};

interface MapViewProps {
  rutaCalculada: Ruta | null;
  origen: Origen | null;
  todosLosPedidos?: Array<{ id: number; nodo_destino: number; cliente_nombre: string; cliente_direccion?: string }>;
  pedidosSeleccionados?: Array<{ id: number; nodo_destino: number; cliente_nombre: string }>;
}

export default function MapView({ rutaCalculada, origen, todosLosPedidos = [], pedidosSeleccionados = [] }: MapViewProps) {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const origenMarkerRef = useRef<L.Marker | null>(null);
  const destinoMarkersRef = useRef<L.Marker[]>([]);
  const routeLayerRef = useRef<L.LayerGroup | L.Polyline | null>(null);
  const [nodos, setNodos] = useState<Nodo[]>([]);
  const [loading, setLoading] = useState(false); // No cargar al inicio
  const [mapReady, setMapReady] = useState(false);

  // Inicializar mapa
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    // Inicializar mapa sin vista fija - se ajustará cuando carguen los nodos
    const map = L.map(mapContainerRef.current, {
      zoomControl: true,
      attributionControl: true,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map);

    // Vista inicial aproximada de toda la provincia de Lima
    map.setView([-12.0464, -77.0428], 10);

    mapRef.current = map;
    
    // Marcar el mapa como listo
    map.whenReady(() => {
      setMapReady(true);
      setLoading(false);
      console.log('Mapa inicializado y listo');
    });
  }, []);

  // Limpiar ruta del mapa
  const clearRoute = () => {
    if (!mapRef.current) return;

    // Eliminar ruta anterior
    if (routeLayerRef.current) {
      if (routeLayerRef.current instanceof L.LayerGroup) {
        routeLayerRef.current.clearLayers();
        mapRef.current.removeLayer(routeLayerRef.current);
      } else {
        mapRef.current.removeLayer(routeLayerRef.current);
      }
      routeLayerRef.current = null;
    }
  };

  // Mostrar marcador de origen
  useEffect(() => {
    if (!mapRef.current || !origen || !mapReady) {
      return;
    }

    // Verificar que las coordenadas son válidas
    if (!isValidCoordinate(origen.latitud, origen.longitud)) {
      console.warn('Coordenadas de origen inválidas:', origen);
      return;
    }

    // Limpiar marcador de origen anterior
    if (origenMarkerRef.current) {
      mapRef.current.removeLayer(origenMarkerRef.current);
      origenMarkerRef.current = null;
    }

    console.log('Mostrando marcador de origen:', origen);

    // Crear marcador de origen con mejor visibilidad
    const marker = L.circleMarker([origen.latitud, origen.longitud], {
      radius: 20,
      fillColor: '#10B981',
      color: '#ffffff',
      weight: 5,
      opacity: 1,
      fillOpacity: 0.95,
    });

    marker.bindPopup(`
      <div style="text-align: left; padding: 0;">
        <div style="font-weight: 600; color: #10B981; margin-bottom: 8px; font-size: 13px; letter-spacing: 0.05em; text-transform: uppercase;">Origen</div>
        <div style="color: #1A3A5C; margin-bottom: 4px; font-size: 14px;">${origen.nombre}</div>
        <div style="color: #808088; font-size: 12px;">Nodo ${origen.nodo_id}</div>
      </div>
    `);

    marker.addTo(mapRef.current);
    origenMarkerRef.current = marker;

    // Ajustar vista para mostrar el origen
    mapRef.current.setView([origen.latitud, origen.longitud], 12);
    
    // Abrir popup automáticamente para que sea más visible
    marker.openPopup();
  }, [origen, mapReady]);

  // Cargar TODOS los nodos del grafo UNA SOLA VEZ al inicializar el mapa
  // Esto evita recargar nodos cada vez que cambia la tienda
  useEffect(() => {
    if (!mapReady || nodos.length > 0) return; // Solo cargar una vez

    const cargarTodosLosNodos = async () => {
      try {
        console.log('🔄 Cargando todos los nodos del grafo (una sola vez)...');
        setLoading(true);
        const todosNodos = await getNodos();
        setNodos(todosNodos);
        console.log(`✅ Todos los nodos del grafo cargados: ${todosNodos.length}`);
      } catch (err) {
        console.error('❌ Error al cargar nodos del grafo:', err);
      } finally {
        setLoading(false);
      }
    };

    cargarTodosLosNodos();
  }, [mapReady]); // Solo cuando el mapa está listo, una sola vez

  // Mostrar marcadores de destinos (TODOS los pedidos, con los seleccionados destacados)
  useEffect(() => {
    if (!mapRef.current || !mapReady) {
      return;
    }

    // Limpiar marcadores anteriores siempre
    destinoMarkersRef.current.forEach((marker) => {
      mapRef.current?.removeLayer(marker);
    });
    destinoMarkersRef.current = [];

    if (todosLosPedidos.length === 0) {
      console.log('📍 No hay pedidos para mostrar');
      return;
    }

    // Si no tenemos los nodos cargados aún, esperar
    if (nodos.length === 0) {
      console.log('⏳ Esperando nodos del grafo...');
      return;
    }
    
    console.log(`📍 Mostrando ${todosLosPedidos.length} pedidos en el mapa`);
    
    // Crear un set de IDs de pedidos seleccionados para búsqueda rápida
    const pedidosSeleccionadosIds = new Set(pedidosSeleccionados.map(p => p.id));

    // Limpiar marcadores anteriores
    destinoMarkersRef.current.forEach((marker) => {
      mapRef.current?.removeLayer(marker);
    });
    destinoMarkersRef.current = [];

    // Crear marcadores para TODOS los pedidos
    todosLosPedidos.forEach((pedido) => {
      const nodo = nodos.find((n: Nodo) => n.id === pedido.nodo_destino);
      if (nodo && isValidCoordinate(nodo.latitud, nodo.longitud)) {
        const estaSeleccionado = pedidosSeleccionadosIds.has(pedido.id);
        
        // Estilo diferente para pedidos seleccionados vs no seleccionados
        const marker = L.circleMarker([nodo.latitud, nodo.longitud], {
          radius: estaSeleccionado ? 16 : 10, // Más grande si está seleccionado
          fillColor: estaSeleccionado ? '#EF4444' : '#94A3B8', // Rojo si seleccionado, gris si no
          color: '#ffffff',
          weight: estaSeleccionado ? 4 : 2,
          opacity: 1,
          fillOpacity: estaSeleccionado ? 0.95 : 0.7, // Más opaco si está seleccionado
        });

        const estado = estaSeleccionado ? 'Seleccionado' : 'Disponible';
        const colorEstado = estaSeleccionado ? '#EF4444' : '#94A3B8';
        
        marker.bindPopup(`
          <div style="text-align: left; padding: 0;">
            <div style="font-weight: 600; color: ${colorEstado}; margin-bottom: 8px; font-size: 13px; letter-spacing: 0.05em; text-transform: uppercase;">${estado}</div>
            <div style="color: #1A3A5C; margin-bottom: 4px; font-size: 14px;">${pedido.cliente_nombre}</div>
            ${pedido.cliente_direccion ? `<div style="color: #808088; font-size: 11px; margin-bottom: 4px;">${pedido.cliente_direccion}</div>` : ''}
            <div style="color: #808088; font-size: 12px;">Pedido #${pedido.id} - Nodo ${nodo.id}</div>
          </div>
        `);

        marker.addTo(mapRef.current!);
        destinoMarkersRef.current.push(marker);
      } else {
        console.warn(`No se encontró nodo ${pedido.nodo_destino} o coordenadas inválidas para pedido ${pedido.id}`);
      }
    });

    // Ajustar vista para mostrar todos los marcadores (origen + todos los destinos)
    const allMarkers = [origenMarkerRef.current, ...destinoMarkersRef.current].filter(Boolean) as L.Layer[];
    if (allMarkers.length > 0) {
      const group = L.featureGroup(allMarkers);
      mapRef.current.fitBounds(group.getBounds().pad(0.15), {
        padding: [50, 50],
        maxZoom: 15,
      });
    } else if (origen && origenMarkerRef.current) {
      // Si solo hay origen, centrar en él
      mapRef.current.setView([origen.latitud, origen.longitud], 12);
    }
  }, [todosLosPedidos, pedidosSeleccionados, nodos, origen, mapReady]);

  // Asegurar que las coordenadas incluyan origen y destino
  const ensureOriginAndDestination = (
    coordenadas: [number, number][],
    origenId: number | null,
    destinoId: number | null
  ): [number, number][] => {
    if (!origenId || !destinoId || coordenadas.length === 0) {
      return coordenadas;
    }

    const nodoOrigen = nodos.find((n: Nodo) => n.id === origenId);
    const nodoDestino = nodos.find((n: Nodo) => n.id === destinoId);
    const result = [...coordenadas];

    // Verificar y agregar origen al inicio
    if (nodoOrigen && result.length > 0) {
      const primerPunto = result[0];
      const distanciaOrigen = calculateDistance(
        primerPunto,
        [nodoOrigen.latitud, nodoOrigen.longitud]
      );
      
      if (distanciaOrigen > 0.001) {
        result.unshift([nodoOrigen.latitud, nodoOrigen.longitud]);
      }
    }

    // Verificar y agregar destino al final
    if (nodoDestino && result.length > 0) {
      const ultimoPunto = result[result.length - 1];
      const distanciaDestino = calculateDistance(
        ultimoPunto,
        [nodoDestino.latitud, nodoDestino.longitud]
      );
      
      if (distanciaDestino > 0.001) {
        result.push([nodoDestino.latitud, nodoDestino.longitud]);
      }
    }

    return result;
  };

  // Procesar segmentos de la ruta
  const processRouteSegments = (segmentos: any[]): [number, number][] => {
    const todasLasCoordenadas: [number, number][] = [];
    
    console.log('Procesando segmentos:', segmentos);
    
    segmentos.forEach((segmento: any, index: number) => {
      if (!segmento || !Array.isArray(segmento) || segmento.length < 2) {
        console.warn(`Segmento ${index} inválido:`, segmento);
        return;
      }

      // Los segmentos vienen como [[lat, lon], [lat, lon], ...]
      const coordenadasSegmento: [number, number][] = segmento.map((coord: any) => {
        if (Array.isArray(coord) && coord.length >= 2) {
          return [Number(coord[0]), Number(coord[1])] as [number, number];
        }
        return null;
      }).filter((coord: [number, number] | null): coord is [number, number] => coord !== null);
      
      if (coordenadasSegmento.length < 2) {
        console.warn(`Segmento ${index} tiene menos de 2 coordenadas válidas`);
        return;
      }

      console.log(`Segmento ${index}: ${coordenadasSegmento.length} puntos`);

      // Evitar duplicados en las uniones
      if (todasLasCoordenadas.length > 0) {
        const ultimoPunto = todasLasCoordenadas[todasLasCoordenadas.length - 1];
        const primerPunto = coordenadasSegmento[0];
        const distancia = calculateDistance(ultimoPunto, primerPunto);
        
        if (distancia < 0.0001) {
          // Si el primer punto del segmento es muy cercano al último punto agregado, omitirlo
          todasLasCoordenadas.push(...coordenadasSegmento.slice(1));
        } else {
          // Agregar todo el segmento
          todasLasCoordenadas.push(...coordenadasSegmento);
        }
      } else {
        // Primer segmento, agregar todas las coordenadas
        todasLasCoordenadas.push(...coordenadasSegmento);
      }
    });

    console.log(`Total de coordenadas procesadas: ${todasLasCoordenadas.length}`);
    return todasLasCoordenadas;
  };

  // Dibujar polyline de ruta
  const drawRoutePolyline = (
    coordenadas: [number, number][],
    options: L.PolylineOptions
  ): L.Polyline | null => {
    if (coordenadas.length < 2) {
      return null;
    }

    return L.polyline(coordenadas, options);
  };

  // Mostrar ruta calculada cuando está disponible
  useEffect(() => {
    if (!rutaCalculada || !mapRef.current) {
      // Si no hay ruta, solo limpiar la ruta anterior
      clearRoute();
      return;
    }

    try {
      if (!mapRef.current) return;

      console.log('Dibujando ruta calculada:', rutaCalculada);
      clearRoute();

      // Crear grupo de capas para la ruta
      const routeGroup = L.layerGroup();
      let coordenadasRuta: [number, number][] = [];

      // Procesar segmentos si existen (preferir segmentos porque tienen más detalle)
      if (rutaCalculada.segmentos && Array.isArray(rutaCalculada.segmentos) && rutaCalculada.segmentos.length > 0) {
        console.log('Usando segmentos para dibujar la ruta');
        coordenadasRuta = processRouteSegments(rutaCalculada.segmentos);
      } 
      // Si no hay segmentos, usar coordenadas principales
      else if (rutaCalculada.coordenadas && Array.isArray(rutaCalculada.coordenadas) && rutaCalculada.coordenadas.length > 1) {
        console.log('Usando coordenadas principales para dibujar la ruta');
        coordenadasRuta = parseCoordinates(rutaCalculada.coordenadas);
      } else {
        console.warn('No hay coordenadas ni segmentos para dibujar la ruta');
      }

      console.log(`Coordenadas finales para dibujar: ${coordenadasRuta.length} puntos`);

      // Dividir la ruta en ida y vuelta
      // La ruta tiene la estructura: [origen, pedido1, pedido2, ..., pedidoN, origen]
      // Necesitamos identificar dónde termina la ida (último pedido) y comienza la vuelta
      if (coordenadasRuta.length >= 2 && rutaCalculada.ruta && rutaCalculada.ruta.length >= 3) {
        const nodosRuta = rutaCalculada.ruta;
        const nodoOrigen = nodosRuta[0];
        const ultimoPedidoIndex = nodosRuta.length - 2; // El penúltimo nodo es el último pedido
        const ultimoPedidoNodoId = nodosRuta[ultimoPedidoIndex];
        
        // Encontrar el punto de división en las coordenadas
        // Buscamos la coordenada que corresponde al último pedido (antes del retorno al origen)
        let indiceDivision = -1;
        
        if (nodos.length > 0) {
          const ultimoPedidoNodo = nodos.find(n => n.id === ultimoPedidoNodoId);
          const origenNodo = nodos.find(n => n.id === nodoOrigen);
          
          if (ultimoPedidoNodo) {
            // Buscar la coordenada más cercana al último pedido
            let distanciaMinima = Infinity;
            let mejorIndice = -1;
            
            // Buscar desde el medio hacia atrás para encontrar el último pedido
            for (let i = Math.floor(coordenadasRuta.length * 0.5); i < coordenadasRuta.length - 10; i++) {
              const distancia = calculateDistance(
                coordenadasRuta[i],
                [ultimoPedidoNodo.latitud, ultimoPedidoNodo.longitud]
              );
              if (distancia < distanciaMinima) {
                distanciaMinima = distancia;
                mejorIndice = i;
              }
            }
            
            // Si encontramos un punto cercano (menos de 1km), usarlo
            if (mejorIndice !== -1 && distanciaMinima < 0.01) {
              indiceDivision = mejorIndice;
            }
          }
          
          // Si no encontramos el punto exacto, buscar el punto más cercano al origen final
          if (indiceDivision === -1 && origenNodo) {
            // Buscar desde el final hacia atrás para encontrar donde comienza el retorno
            let distanciaMinimaOrigen = Infinity;
            for (let i = Math.floor(coordenadasRuta.length * 0.7); i < coordenadasRuta.length; i++) {
              const distancia = calculateDistance(
                coordenadasRuta[i],
                [origenNodo.latitud, origenNodo.longitud]
              );
              if (distancia < distanciaMinimaOrigen) {
                distanciaMinimaOrigen = distancia;
                // El punto de división es justo antes de acercarse al origen
                if (distancia < 0.01) {
                  indiceDivision = Math.max(0, i - 5); // Retroceder un poco
                  break;
                }
              }
            }
          }
        }
        
        // Si aún no encontramos el punto de división, usar una aproximación basada en la cantidad de pedidos
        if (indiceDivision === -1 || indiceDivision === 0 || indiceDivision >= coordenadasRuta.length - 5) {
          // Si hay N pedidos, la ida debería ser aproximadamente N/(N+1) de la ruta
          // (N segmentos de ida vs 1 segmento de vuelta)
          const numPedidos = nodosRuta.length - 2; // Total de nodos menos origen inicial y final
          const proporcionIda = numPedidos > 0 ? numPedidos / (numPedidos + 1) : 0.8;
          indiceDivision = Math.floor(coordenadasRuta.length * proporcionIda);
          // Asegurar que no sea muy cerca del final
          indiceDivision = Math.min(indiceDivision, coordenadasRuta.length - 10);
        }
        
        // Dividir coordenadas en ida y vuelta
        const coordenadasIda = coordenadasRuta.slice(0, indiceDivision + 1);
        const coordenadasVuelta = coordenadasRuta.slice(indiceDivision);
        
        console.log(`🟢 Ruta de ida: ${coordenadasIda.length} puntos`);
        console.log(`🔴 Ruta de vuelta: ${coordenadasVuelta.length} puntos`);
        
        // Dibujar ruta de ida (verde - desde origen hasta último pedido)
        if (coordenadasIda.length >= 2) {
          const polylineIda = drawRoutePolyline(coordenadasIda, {
            color: '#10B981', // Verde para la ida
            weight: 6,
            opacity: 0.9,
            smoothFactor: 1.0,
            lineJoin: 'round',
            lineCap: 'round',
          });

          if (polylineIda) {
            routeGroup.addLayer(polylineIda);
            console.log('✅ Ruta de ida dibujada (verde)');
          }
        }
        
        // Dibujar ruta de vuelta (rojo - desde último pedido hasta origen)
        if (coordenadasVuelta.length >= 2) {
          const polylineVuelta = drawRoutePolyline(coordenadasVuelta, {
            color: '#EF4444', // Rojo para la vuelta
            weight: 6,
            opacity: 0.9,
            smoothFactor: 1.0,
            lineJoin: 'round',
            lineCap: 'round',
          });

          if (polylineVuelta) {
            routeGroup.addLayer(polylineVuelta);
            console.log('✅ Ruta de vuelta dibujada (rojo)');
          }
        }
      } else {
        // Fallback: dibujar toda la ruta de un solo color si no podemos dividirla
        console.warn('⚠️ No se pudo dividir la ruta, dibujando toda en un solo color');
        if (coordenadasRuta.length >= 2) {
          const polyline = drawRoutePolyline(coordenadasRuta, {
            color: '#EF4444',
            weight: 6,
            opacity: 0.9,
            smoothFactor: 1.0,
            lineJoin: 'round',
            lineCap: 'round',
          });

          if (polyline) {
            routeGroup.addLayer(polyline);
            console.log('Polyline agregado al mapa (fallback)');
          }
        }
      }

      // Agregar el grupo al mapa si tiene capas
      if (routeGroup.getLayers().length > 0) {
        routeGroup.addTo(mapRef.current);
        routeLayerRef.current = routeGroup;

        // Agregar popup con información de la ruta
        const firstLayer = routeGroup.getLayers()[0] as L.Polyline;
        const popupContent = `
          <div style="padding: 0;">
            <div style="font-weight: 600; color: #1A3A5C; margin-bottom: 12px; font-size: 14px; letter-spacing: 0.02em;">Ruta Optimizada</div>
            <div style="border-top: 1px solid rgba(26, 58, 92, 0.1); margin: 12px 0;"></div>
            <div style="color: #1A3A5C; margin-bottom: 8px; font-size: 13px;"><strong>Distancia:</strong> ${rutaCalculada.distancia_total.toFixed(2)} km</div>
            <div style="color: #1A3A5C; margin-bottom: 8px; font-size: 13px;"><strong>Puntos:</strong> ${rutaCalculada.ruta.length}</div>
            <div style="color: #808088; margin-top: 12px; font-size: 11px; letter-spacing: 0.05em; text-transform: uppercase;">Ruta con retorno al origen</div>
          </div>
        `;
        firstLayer.bindPopup(popupContent);
      }

      // Ajustar vista para mostrar la ruta y los marcadores
      const allLayers: L.Layer[] = [];
      routeGroup.eachLayer((layer: L.Layer) => allLayers.push(layer));
      if (origenMarkerRef.current) allLayers.push(origenMarkerRef.current);
      destinoMarkersRef.current.forEach((marker) => allLayers.push(marker));
      
      if (allLayers.length > 0) {
        adjustMapBounds(mapRef.current, allLayers, 0.15);
      }
    } catch (err) {
      console.error('Error al mostrar ruta:', err);
    }
  }, [rutaCalculada]);

  return (
    <div className="relative w-full h-full bg-white">
      <div ref={mapContainerRef} className="w-full h-full" />
      {loading && (
        <div className="absolute inset-0 bg-white/95 backdrop-blur-sm flex items-center justify-center z-[1000]">
          <div className="text-base text-blue-dark font-medium tracking-wide">Cargando mapa...</div>
        </div>
      )}
    </div>
  );
}

