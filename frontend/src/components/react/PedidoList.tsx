import type { Pedido } from '../../services/api';

interface PedidoListProps {
  tienda: 'Saga' | 'Ripley';
  pedidos: Pedido[]; // Recibir pedidos como prop en lugar de cargarlos
  pedidosSeleccionados: number[];
  onPedidosChange: (pedidoIds: number[]) => void;
}

export default function PedidoList({ tienda, pedidos, pedidosSeleccionados, onPedidosChange }: PedidoListProps) {
  // Ya no necesitamos estado local ni cargar pedidos - los recibimos como prop

  const handleTogglePedido = (pedidoId: number) => {
    if (pedidosSeleccionados.includes(pedidoId)) {
      onPedidosChange(pedidosSeleccionados.filter(id => id !== pedidoId));
    } else {
      onPedidosChange([...pedidosSeleccionados, pedidoId]);
    }
  };

  return (
    <div className="flex-1">
      <h3 className="text-2xl font-bold text-blue-dark mb-4 tracking-tight">
        Pedidos ({pedidos.length})
      </h3>
      <p className="text-sm text-blue-medium mb-6">
        Selecciona los pedidos que deseas entregar ({pedidosSeleccionados.length} seleccionados)
      </p>
      {pedidos.length === 0 ? (
        <p className="py-12 text-center text-blue-medium">No hay pedidos disponibles</p>
      ) : (
        <ul className="space-y-4">
          {pedidos.map((pedido) => {
            const isSelected = pedidosSeleccionados.includes(pedido.id);
            return (
              <li
                key={pedido.id}
                className={`bg-white rounded-xl p-5 shadow-md hover:shadow-xl transition-all duration-300 border-2 ${
                  isSelected 
                    ? 'border-coral shadow-xl' 
                    : 'border-blue-primary/10 hover:border-blue-primary/30'
                }`}
              >
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => handleTogglePedido(pedido.id)}
                    className="mt-1 w-5 h-5 text-coral border-blue-primary/30 rounded focus:ring-coral focus:ring-2 cursor-pointer"
                  />
                  <div className="flex-1">
                    <div className="flex justify-between items-center mb-3">
                      <strong className="text-lg font-bold text-blue-dark">Pedido #{pedido.id}</strong>
                      <span className="px-3 py-1 bg-blue-primary/10 text-blue-dark rounded-full text-xs font-semibold uppercase tracking-wide">
                        {pedido.tienda}
                      </span>
                    </div>
                    <div className="space-y-2">
                      <p className="text-sm font-semibold text-blue-dark">{pedido.cliente_nombre}</p>
                      <p className="text-xs text-blue-medium flex items-start gap-2">
                        <span>📍</span>
                        <span>{pedido.cliente_direccion}</span>
                      </p>
                      {pedido.cliente_telefono && (
                        <p className="text-xs text-blue-medium flex items-center gap-2">
                          <span>📞</span>
                          <span>{pedido.cliente_telefono}</span>
                        </p>
                      )}
                      <p className="flex items-center gap-2 text-blue-medium text-xs mt-3 pt-3 border-t border-blue-primary/10">
                        <span>📅</span>
                        {pedido.fecha}
                      </p>
                      <p className="text-xs text-blue-medium">
                        <strong>Destino:</strong> Nodo {pedido.nodo_destino}
                      </p>
                    </div>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

