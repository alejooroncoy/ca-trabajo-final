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
  pedidosSeleccionados?: Array<{ id: number; nodo_destino: number; cliente_nombre: string }>;
}

export default function MapView({ rutaCalculada, origen, pedidosSeleccionados = [] }: MapViewProps) {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const origenMarkerRef = useRef<L.Marker | null>(null);
  const destinoMarkersRef = useRef<L.Marker[]>([]);
  const routeLayerRef = useRef<L.LayerGroup | L.Polyline | null>(null);
  const [nodos, setNodos] = useState<Nodo[]>([]);
  const [loading, setLoading] = useState(true);

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

    // Cargar nodos después de que el mapa esté listo
    map.whenReady(() => {
      loadNodos();
    });
  }, []);

  // Cargar nodos (solo para obtener coordenadas cuando sea necesario, no para mostrar)
  const loadNodos = async () => {
    try {
      setLoading(true);
      const nodosData = await getNodos();
      setNodos(nodosData);
    } catch (err) {
      console.error('Error al cargar nodos:', err);
    } finally {
      setLoading(false);
    }
  };

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
    if (!mapRef.current || !origen) return;

    // Limpiar marcador de origen anterior
    if (origenMarkerRef.current) {
      mapRef.current.removeLayer(origenMarkerRef.current);
    }

    // Crear marcador de origen
    const marker = L.circleMarker([origen.latitud, origen.longitud], {
      radius: 18,
      fillColor: '#10B981',
      color: '#ffffff',
      weight: 4,
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
  }, [origen]);

  // Mostrar marcadores de destinos (pedidos seleccionados)
  useEffect(() => {
    if (!mapRef.current || pedidosSeleccionados.length === 0) {
      // Limpiar marcadores de destino si no hay pedidos seleccionados
      destinoMarkersRef.current.forEach((marker) => {
        mapRef.current?.removeLayer(marker);
      });
      destinoMarkersRef.current = [];
      return;
    }

    // Limpiar marcadores anteriores
    destinoMarkersRef.current.forEach((marker) => {
      mapRef.current?.removeLayer(marker);
    });
    destinoMarkersRef.current = [];

    // Crear marcadores para cada pedido seleccionado
    pedidosSeleccionados.forEach((pedido) => {
      const nodo = nodos.find((n: Nodo) => n.id === pedido.nodo_destino);
      if (nodo && isValidCoordinate(nodo.latitud, nodo.longitud)) {
        const marker = L.circleMarker([nodo.latitud, nodo.longitud], {
          radius: 14,
          fillColor: '#EF4444',
          color: '#ffffff',
          weight: 3,
          opacity: 1,
          fillOpacity: 0.95,
        });

        marker.bindPopup(`
          <div style="text-align: left; padding: 0;">
            <div style="font-weight: 600; color: #EF4444; margin-bottom: 8px; font-size: 13px; letter-spacing: 0.05em; text-transform: uppercase;">Destino</div>
            <div style="color: #1A3A5C; margin-bottom: 4px; font-size: 14px;">${pedido.cliente_nombre}</div>
            <div style="color: #808088; font-size: 12px;">Pedido #${pedido.id} - Nodo ${nodo.id}</div>
          </div>
        `);

        marker.addTo(mapRef.current!);
        destinoMarkersRef.current.push(marker);
      }
    });

    // Ajustar vista para mostrar todos los marcadores (origen + destinos)
    if (origen && destinoMarkersRef.current.length > 0) {
      const allMarkers = [origenMarkerRef.current, ...destinoMarkersRef.current].filter(Boolean) as L.Marker[];
      if (allMarkers.length > 0) {
        const group = L.featureGroup(allMarkers);
        mapRef.current.fitBounds(group.getBounds().pad(0.1), {
          padding: [50, 50],
          maxZoom: 15,
        });
      }
    }
  }, [pedidosSeleccionados, nodos, origen]);

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
    
    segmentos.forEach((segmento: any) => {
      if (!segmento || !Array.isArray(segmento) || segmento.length < 2) {
        return;
      }

      const coordenadasSegmento = parseCoordinates(segmento);
      
      if (coordenadasSegmento.length < 2) {
        return;
      }

      // Evitar duplicados en las uniones
      if (todasLasCoordenadas.length > 0) {
        const ultimoPunto = todasLasCoordenadas[todasLasCoordenadas.length - 1];
        const primerPunto = coordenadasSegmento[0];
        const distancia = calculateDistance(ultimoPunto, primerPunto);
        
        if (distancia < 0.0001) {
          todasLasCoordenadas.push(...coordenadasSegmento.slice(1));
        } else {
          todasLasCoordenadas.push(...coordenadasSegmento);
        }
      } else {
        todasLasCoordenadas.push(...coordenadasSegmento);
      }
    });

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

      clearRoute();


      // Crear grupo de capas para la ruta
      const routeGroup = L.layerGroup();
      let coordenadasRuta: [number, number][] = [];

      // Procesar segmentos si existen
      if (rutaCalculada.segmentos && rutaCalculada.segmentos.length > 0) {
        coordenadasRuta = processRouteSegments(rutaCalculada.segmentos);
      } 
      // Si no hay segmentos, usar coordenadas principales
      else if (rutaCalculada.coordenadas && Array.isArray(rutaCalculada.coordenadas) && rutaCalculada.coordenadas.length > 1) {
        coordenadasRuta = parseCoordinates(rutaCalculada.coordenadas);
      }

      // Dibujar polyline de la ruta
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

