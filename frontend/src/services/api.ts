const API_BASE = 'http://localhost:8000/api';

export interface Pedido {
  id: number;
  tienda: 'Saga' | 'Ripley';
  fecha: string;
  nodos: number[];
  ruta_optimizada?: number[] | null;
}

export interface Ruta {
  pedido_id: number;
  ruta: number[];
  distancia_total: number;
  coordenadas: [number, number][];
  segmentos?: [number, number][][];  // Segmentos del camino real en el grafo
}

export interface Nodo {
  id: number;
  latitud: number;
  longitud: number;
}

export interface Arista {
  origen: number;
  destino: number;
  peso: number;
}

// Pedidos
export async function getPedidos(tienda?: string): Promise<Pedido[]> {
  const url = tienda ? `${API_BASE}/pedidos?tienda=${tienda}` : `${API_BASE}/pedidos`;
  const response = await fetch(url);
  if (!response.ok) throw new Error('Error al obtener pedidos');
  return response.json();
}

export async function getPedido(id: number): Promise<Pedido> {
  const response = await fetch(`${API_BASE}/pedidos/${id}`);
  if (!response.ok) throw new Error('Error al obtener pedido');
  return response.json();
}

export async function createPedido(pedido: Omit<Pedido, 'id'>): Promise<Pedido> {
  const response = await fetch(`${API_BASE}/pedidos`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(pedido),
  });
  if (!response.ok) throw new Error('Error al crear pedido');
  return response.json();
}

// Rutas
export async function calcularRuta(pedidoId: number): Promise<Ruta> {
  const response = await fetch(`${API_BASE}/rutas/calcular`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pedido_id: pedidoId }),
  });
  if (!response.ok) throw new Error('Error al calcular ruta');
  return response.json();
}

export async function getRutaPedido(pedidoId: number): Promise<Ruta> {
  const response = await fetch(`${API_BASE}/rutas/pedido/${pedidoId}`);
  if (!response.ok) throw new Error('Error al obtener ruta');
  return response.json();
}

// Grafo
export async function getNodos(): Promise<Nodo[]> {
  const response = await fetch(`${API_BASE}/grafo/nodos`);
  if (!response.ok) throw new Error('Error al obtener nodos');
  return response.json();
}

export async function getAristas(): Promise<Arista[]> {
  const response = await fetch(`${API_BASE}/grafo/aristas`);
  if (!response.ok) throw new Error('Error al obtener aristas');
  return response.json();
}

