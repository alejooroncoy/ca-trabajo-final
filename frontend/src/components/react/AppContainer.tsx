import { useState, useEffect } from 'react';
import MapView from './MapView';
import PedidoList from './PedidoList';
import type { Pedido, Origen, Ruta } from '../../services/api';
import { getOrigenes, calcularRutaMultiple, getPedidos } from '../../services/api';

export default function AppContainer() {
  const [tiendaSeleccionada, setTiendaSeleccionada] = useState<'Saga' | 'Ripley' | null>(null);
  const [algoritmo, setAlgoritmo] = useState<string>('dijkstra');
  const [origenes, setOrigenes] = useState<{ Saga: Origen; Ripley: Origen } | null>(null);
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [pedidosSeleccionados, setPedidosSeleccionados] = useState<number[]>([]);
  const [rutaCalculada, setRutaCalculada] = useState<Ruta | null>(null);
  const [calculando, setCalculando] = useState(false);

  // Cargar orígenes y pedidos al montar
  useEffect(() => {
    getOrigenes()
      .then(setOrigenes)
      .catch(err => console.error('Error al cargar orígenes:', err));
  }, []);

  // Cargar pedidos cuando cambia la tienda seleccionada
  useEffect(() => {
    if (tiendaSeleccionada) {
      console.log(`🔄 Cargando pedidos para ${tiendaSeleccionada}...`);
      getPedidos(tiendaSeleccionada)
        .then(data => {
          console.log(`✅ Pedidos cargados para ${tiendaSeleccionada}:`, data.length);
          setPedidos(data);
        })
        .catch(err => {
          console.error('Error al cargar pedidos:', err);
          setPedidos([]);
        });
    } else {
      setPedidos([]);
    }
  }, [tiendaSeleccionada]);

  const handleTiendaChange = (tienda: 'Saga' | 'Ripley') => {
    setTiendaSeleccionada(tienda);
    // Limpiar selección de pedidos y ruta cuando cambia la tienda
    setPedidosSeleccionados([]);
    setRutaCalculada(null);
  };

  const handleAlgorithmChange = (nuevoAlgoritmo: string) => {
    setAlgoritmo(nuevoAlgoritmo);
    // Limpiar ruta cuando cambia el algoritmo para forzar recálculo
    setRutaCalculada(null);
  };

  const handlePedidosChange = (pedidoIds: number[]) => {
    setPedidosSeleccionados(pedidoIds);
    // Limpiar ruta cuando cambian los pedidos seleccionados
    setRutaCalculada(null);
  };

  const handleCalcularRuta = async () => {
    if (!tiendaSeleccionada || !origenes || pedidosSeleccionados.length === 0) {
      alert('Por favor selecciona una tienda y al menos un pedido');
      return;
    }

    setCalculando(true);
    setRutaCalculada(null); // Limpiar ruta anterior
    
    try {
      const nodoOrigen = origenes[tiendaSeleccionada].nodo_id;
      console.log('Calculando ruta múltiple:', {
        pedidos: pedidosSeleccionados,
        nodoOrigen,
        tienda: tiendaSeleccionada,
        algoritmo: algoritmo
      });
      
      const ruta = await calcularRutaMultiple(pedidosSeleccionados, nodoOrigen, algoritmo);
      console.log('Ruta calculada recibida:', ruta);
      
      setRutaCalculada(ruta);
    } catch (error) {
      console.error('Error al calcular ruta:', error);
      alert('Error al calcular la ruta. Por favor intenta de nuevo.');
    } finally {
      setCalculando(false);
    }
  };

  return (
    <div className="flex w-full flex-1 overflow-hidden">
      <div className="w-[70%] h-full relative bg-white border-r border-blue-primary/10">
        {origenes ? (
          <MapView 
            rutaCalculada={rutaCalculada}
            origen={tiendaSeleccionada ? origenes[tiendaSeleccionada] : null}
            todosLosPedidos={tiendaSeleccionada ? pedidos.map(p => ({ 
              id: p.id, 
              nodo_destino: p.nodo_destino, 
              cliente_nombre: p.cliente_nombre,
              cliente_direccion: p.cliente_direccion
            })) : []}
            pedidosSeleccionados={pedidosSeleccionados.map(id => {
              const pedido = pedidos.find(p => p.id === id);
              return pedido ? { id: pedido.id, nodo_destino: pedido.nodo_destino, cliente_nombre: pedido.cliente_nombre } : null;
            }).filter(Boolean) as Array<{ id: number; nodo_destino: number; cliente_nombre: string }>}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <div className="text-blue-medium">Cargando mapa...</div>
          </div>
        )}
      </div>
      <div className="w-[30%] h-full bg-white/80 backdrop-blur-sm flex flex-col p-6 md:p-8 overflow-y-auto custom-scrollbar">
        {/* Selector de Tienda */}
        <div className="mb-8 pb-6 border-b border-blue-primary/10">
          <label className="flex items-center gap-2 mb-3 font-semibold text-sm text-blue-dark uppercase tracking-wide">
            <span>🏪</span>
            Seleccionar Tienda
          </label>
          <div className="flex gap-3">
            <button
              onClick={() => handleTiendaChange('Saga')}
              className={`flex-1 px-4 py-3 rounded-lg text-sm font-semibold transition-all duration-300 ${
                tiendaSeleccionada === 'Saga'
                  ? 'bg-blue-primary text-white shadow-lg'
                  : 'bg-blue-primary/10 text-blue-dark hover:bg-blue-primary/20'
              }`}
            >
              Saga
            </button>
            <button
              onClick={() => handleTiendaChange('Ripley')}
              className={`flex-1 px-4 py-3 rounded-lg text-sm font-semibold transition-all duration-300 ${
                tiendaSeleccionada === 'Ripley'
                  ? 'bg-coral text-white shadow-lg'
                  : 'bg-coral/10 text-coral-dark hover:bg-coral/20'
              }`}
            >
              Ripley
            </button>
          </div>
          {tiendaSeleccionada && origenes && (
            <p className="mt-2 text-xs text-blue-medium">
              Origen: {origenes[tiendaSeleccionada].nombre}
            </p>
          )}
        </div>

        {/* Selector de Algoritmo */}
        <div className="mb-8 pb-6 border-b border-blue-primary/10">
          <label htmlFor="algorithm-selector" className="flex items-center gap-2 mb-3 font-semibold text-sm text-blue-dark uppercase tracking-wide">
            <span>⚙️</span>
            Algoritmo de rutas
          </label>
          <select
            id="algorithm-selector"
            value={algoritmo}
            onChange={(e) => handleAlgorithmChange(e.target.value)}
            className="w-full px-4 py-3 border border-blue-primary/20 rounded-lg text-sm bg-white text-blue-dark font-medium transition-all duration-300 hover:border-blue-primary/40 focus:outline-none focus:ring-2 focus:ring-blue-primary/20 focus:border-blue-primary cursor-pointer"
          >
            <option value="dijkstra">Dijkstra</option>
            <option value="floyd_warshall">Floyd-Warshall</option>
          </select>
          <p className="mt-2 text-xs text-blue-medium">
            {algoritmo === 'dijkstra' 
              ? 'Algoritmo eficiente para calcular el camino más corto entre dos puntos'
              : 'Algoritmo que encuentra todos los caminos más cortos entre todos los pares de nodos'}
          </p>
        </div>

        {/* Lista de Pedidos */}
        {tiendaSeleccionada ? (
          <>
            <PedidoList 
              tienda={tiendaSeleccionada}
              pedidos={pedidos}
              pedidosSeleccionados={pedidosSeleccionados}
              onPedidosChange={handlePedidosChange}
            />
            
            {/* Botón Calcular Ruta */}
            {pedidosSeleccionados.length > 0 && (
              <div className="mt-6 pt-6 border-t border-blue-primary/10">
                <button
                  onClick={handleCalcularRuta}
                  disabled={calculando}
                  className="w-full px-6 py-3 bg-gradient-to-r from-blue-primary to-coral text-white rounded-lg font-semibold transition-all duration-300 hover:shadow-xl hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {calculando ? 'Calculando ruta...' : `Calcular Ruta (${pedidosSeleccionados.length} pedidos)`}
                </button>
                {rutaCalculada && (
                  <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-sm font-semibold text-green-800">
                      Ruta calculada: {rutaCalculada.distancia_total.toFixed(2)} km
                    </p>
                    <p className="text-xs text-green-600 mt-1">
                      {rutaCalculada.ruta.length} puntos en la ruta
                    </p>
                  </div>
                )}
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-12">
            <p className="text-blue-medium">Por favor selecciona una tienda para comenzar</p>
          </div>
        )}
      </div>
    </div>
  );
}

