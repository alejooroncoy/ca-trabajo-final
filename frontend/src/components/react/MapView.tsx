import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getNodos, getAristas, calcularRuta, type Pedido, type Nodo, type Ruta, type Arista } from '../../services/api';

// Fix para iconos de Leaflet (usando URLs públicas)
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

interface MapViewProps {
  selectedPedido: Pedido | null;
}

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

export default function MapView({ selectedPedido }: MapViewProps) {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const markersRef = useRef<L.Marker[]>([]);
  const edgesLayerRef = useRef<L.LayerGroup | null>(null);
  const routeLayerRef = useRef<L.LayerGroup | L.Polyline | null>(null);
  const highlightedMarkersRef = useRef<L.Marker[]>([]);
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

  // Cargar nodos y aristas del grafo
  const loadNodos = async () => {
    try {
      setLoading(true);
      const [nodosData, aristasData] = await Promise.all([
        getNodos(),
        getAristas()
      ]);
      
      setNodos(nodosData);
      
      if (!mapRef.current || nodosData.length === 0) {
        setLoading(false);
        return;
      }

      // Limpiar marcadores anteriores
      markersRef.current.forEach((marker: L.Marker) => {
        mapRef.current?.removeLayer(marker);
      });
      markersRef.current = [];

      // Limpiar aristas anteriores
      if (edgesLayerRef.current) {
        mapRef.current.removeLayer(edgesLayerRef.current);
      }
      edgesLayerRef.current = L.layerGroup().addTo(mapRef.current);

      // Crear un mapa de nodos por ID para acceso rápido
      const nodosMap = new Map(nodosData.map((n: Nodo) => [n.id, n]));

      // Agregar todos los marcadores
      nodosData.forEach((nodo: Nodo) => {
        if (nodo.latitud && nodo.longitud && isValidCoordinate(nodo.latitud, nodo.longitud)) {
          const marker = L.marker([nodo.latitud, nodo.longitud], {
            title: `Nodo ${nodo.id}`,
          }).addTo(mapRef.current!);
          
          marker.bindPopup(`Nodo ${nodo.id}`);
          markersRef.current.push(marker);
        } else {
          console.warn(`Nodo ${nodo.id} tiene coordenadas inválidas:`, nodo.latitud, nodo.longitud);
        }
      });
      
      // Dibujar aristas (conexiones entre nodos)
      aristasData.forEach((arista: Arista) => {
        const nodoOrigen = nodosMap.get(arista.origen);
        const nodoDestino = nodosMap.get(arista.destino);
        
        if (nodoOrigen && nodoDestino &&
          isValidCoordinate(nodoOrigen.latitud, nodoOrigen.longitud) &&
          isValidCoordinate(nodoDestino.latitud, nodoDestino.longitud)) {
          const polyline = L.polyline(
            [
              [nodoOrigen.latitud, nodoOrigen.longitud], 
              [nodoDestino.latitud, nodoDestino.longitud]
            ],
            {
              color: '#7f8c8d',
              weight: 2,
              opacity: 0.6,
              smoothFactor: 1.0,
              interactive: false,
            }
          );
          edgesLayerRef.current!.addLayer(polyline);
        }
      });

      // Ajustar vista para mostrar todos los marcadores
      if (markersRef.current.length > 0) {
        setTimeout(() => {
          if (mapRef.current && markersRef.current.length > 0) {
            adjustMapBounds(mapRef.current, markersRef.current, 0);
          }
        }, 100);
      }
    } catch (err) {
      console.error('Error al cargar nodos:', err);
    } finally {
      setLoading(false);
    }
  };

  // Limpiar capas del mapa
  const clearMapLayers = () => {
    if (!mapRef.current) return;

    // Ocultar marcadores del grafo
    markersRef.current.forEach((marker: L.Marker) => {
      if (mapRef.current?.hasLayer(marker)) {
        mapRef.current.removeLayer(marker);
      }
    });

    // Ocultar aristas del grafo
    if (edgesLayerRef.current && mapRef.current.hasLayer(edgesLayerRef.current)) {
      mapRef.current.removeLayer(edgesLayerRef.current);
    }

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

    // Eliminar marcadores destacados
    highlightedMarkersRef.current.forEach((marker: L.Marker) => {
      mapRef.current?.removeLayer(marker);
    });
    highlightedMarkersRef.current = [];
  };

  // Crear marcador destacado
  const createHighlightMarker = (
    nodo: Nodo,
    color: string,
    label: string,
    pedidoId: number
  ): L.CircleMarker => {
    const marker = L.circleMarker([nodo.latitud, nodo.longitud], {
      radius: 14,
      fillColor: color,
      color: '#ffffff',
      weight: 3,
      opacity: 1,
      fillOpacity: 0.95,
    });
    
    marker.bindPopup(`
      <div style="text-align: left; padding: 0;">
        <div style="font-weight: 600; color: ${color}; margin-bottom: 8px; font-size: 13px; letter-spacing: 0.05em; text-transform: uppercase;">${label}</div>
        <div style="color: #ffffff; margin-bottom: 4px; font-size: 14px;">Nodo ${nodo.id}</div>
        <div style="color: #808088; font-size: 12px;">Pedido #${pedidoId}</div>
      </div>
    `);
    
    return marker;
  };

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

  // Calcular y mostrar ruta cuando se selecciona un pedido
  useEffect(() => {
    if (!selectedPedido || !mapRef.current) return;

    const calculateAndShowRoute = async () => {
      try {
        if (!mapRef.current) return;

        clearMapLayers();

        // Calcular ruta
        const ruta = await calcularRuta(selectedPedido.id);
        
        // Verificar discrepancia entre nodos del pedido y nodos de la ruta
        if (selectedPedido.nodos && selectedPedido.nodos.length > 1 && ruta.ruta && ruta.ruta.length === 1) {
          console.warn(`⚠️ ADVERTENCIA: El pedido tiene ${selectedPedido.nodos.length} nodos pero la ruta solo devuelve ${ruta.ruta.length} nodo(s).`);
        }

        // Resaltar origen y destino
        const origenId = selectedPedido.nodos && selectedPedido.nodos.length >= 2 
          ? selectedPedido.nodos[0] 
          : null;
        const destinoId = selectedPedido.nodos && selectedPedido.nodos.length >= 2 
          ? selectedPedido.nodos[1] 
          : null;
        
        if (origenId && destinoId) {
          const nodoOrigen = nodos.find((n: Nodo) => n.id === origenId);
          const nodoDestino = nodos.find((n: Nodo) => n.id === destinoId);
          
          if (nodoOrigen) {
            const markerOrigen = createHighlightMarker(nodoOrigen, '#10B981', 'Origen', selectedPedido.id);
            markerOrigen.addTo(mapRef.current);
            highlightedMarkersRef.current.push(markerOrigen as unknown as L.Marker);
          }
          
          if (nodoDestino) {
            const markerDestino = createHighlightMarker(nodoDestino, '#EF4444', 'Destino', selectedPedido.id);
            markerDestino.addTo(mapRef.current);
            highlightedMarkersRef.current.push(markerDestino as unknown as L.Marker);
          }
        }

        if (!mapRef.current) return;

        // Crear grupo de capas para la ruta
        const routeGroup = L.layerGroup();
        let coordenadasRuta: [number, number][] = [];

        // Procesar segmentos si existen
        if (ruta.segmentos && ruta.segmentos.length > 0) {
          coordenadasRuta = processRouteSegments(ruta.segmentos);
          coordenadasRuta = ensureOriginAndDestination(coordenadasRuta, origenId, destinoId);
        } 
        // Si no hay segmentos, usar coordenadas principales
        else if (ruta.coordenadas && Array.isArray(ruta.coordenadas) && ruta.coordenadas.length > 1) {
          coordenadasRuta = parseCoordinates(ruta.coordenadas);
          coordenadasRuta = ensureOriginAndDestination(coordenadasRuta, origenId, destinoId);
        }

        // Dibujar polyline de la ruta
        if (coordenadasRuta.length >= 2) {
          const polyline = drawRoutePolyline(coordenadasRuta, {
            color: ruta.segmentos && ruta.segmentos.length > 0 ? '#ffffff' : '#EF4444',
            weight: ruta.segmentos && ruta.segmentos.length > 0 ? 5 : 8,
            opacity: ruta.segmentos && ruta.segmentos.length > 0 ? 0.9 : 1.0,
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
              <div style="font-weight: 600; color: #808088; margin-bottom: 12px; font-size: 14px; letter-spacing: 0.02em;">Ruta Optimizada</div>
              <div style="border-top: 1px solid rgba(255, 255, 255, 0.1); margin: 12px 0;"></div>
              <div style="color: #808088; margin-bottom: 8px; font-size: 13px;"><strong>Distancia:</strong> ${ruta.distancia_total.toFixed(2)} km</div>
              <div style="color: #808088; margin-bottom: 8px; font-size: 13px;"><strong>Nodos:</strong> ${ruta.ruta.length}</div>
              <div style="color: #808088; margin-top: 12px; font-size: 11px; letter-spacing: 0.05em; text-transform: uppercase;">Camino más rápido</div>
            </div>
          `;
          firstLayer.bindPopup(popupContent).openPopup();
        }

        // Ajustar vista para mostrar la ruta y los marcadores destacados
        const allLayers: L.Layer[] = [];
        routeGroup.eachLayer((layer: L.Layer) => allLayers.push(layer));
        highlightedMarkersRef.current.forEach((marker: L.Marker) => allLayers.push(marker));
        
        if (allLayers.length > 0) {
          adjustMapBounds(mapRef.current, allLayers, 0.15);
        }
      } catch (err) {
        console.error('Error al calcular ruta:', err);
      }
    };

    calculateAndShowRoute();
  }, [selectedPedido, nodos]);

  // Restaurar todos los marcadores y aristas cuando no hay pedido seleccionado
  useEffect(() => {
    if (selectedPedido || !mapRef.current) return;

    // Restaurar todos los marcadores
    markersRef.current.forEach((marker: L.Marker) => {
      if (!mapRef.current?.hasLayer(marker)) {
        marker.addTo(mapRef.current!);
      }
    });

    // Restaurar todas las aristas
    if (edgesLayerRef.current && !mapRef.current.hasLayer(edgesLayerRef.current)) {
      edgesLayerRef.current.addTo(mapRef.current);
    }

    // Limpiar ruta anterior si existe
    if (routeLayerRef.current) {
      if (routeLayerRef.current instanceof L.LayerGroup) {
        routeLayerRef.current.clearLayers();
        mapRef.current.removeLayer(routeLayerRef.current);
      } else {
        mapRef.current.removeLayer(routeLayerRef.current);
      }
      routeLayerRef.current = null;
    }

    // Limpiar marcadores destacados
    highlightedMarkersRef.current.forEach((marker: L.Marker) => {
      mapRef.current?.removeLayer(marker);
    });
    highlightedMarkersRef.current = [];

    // Ajustar vista para mostrar todos los marcadores
    if (markersRef.current.length > 0) {
      setTimeout(() => {
        if (mapRef.current && markersRef.current.length > 0) {
          adjustMapBounds(mapRef.current, markersRef.current, 0);
        }
      }, 100);
    }
  }, [selectedPedido?.id]);

  return (
    <div className="map-container-wrapper">
      <div ref={mapContainerRef} className="map-container" />
      {loading && (
        <div className="map-loading-overlay">
          <div className="map-loading">Cargando mapa...</div>
        </div>
      )}
    </div>
  );
}

