import { useState, useEffect } from 'react';
import { getPedidos, type Pedido } from '../../services/api';

interface PedidoListProps {
  tiendaFilter: string;
  onPedidoSelect: (pedido: Pedido) => void;
}

export default function PedidoList({ tiendaFilter, onPedidoSelect }: PedidoListProps) {
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  useEffect(() => {
    loadPedidos();
  }, [tiendaFilter]);

  const loadPedidos = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getPedidos(tiendaFilter || undefined);
      setPedidos(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar pedidos');
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (pedido: Pedido) => {
    setSelectedId(pedido.id);
    onPedidoSelect(pedido);
  };

  if (loading) {
    return <div className="pedido-list-loading">Cargando pedidos...</div>;
  }

  if (error) {
    return <div className="pedido-list-error">Error: {error}</div>;
  }

  return (
    <div className="pedido-list">
      <h3>Pedidos ({pedidos.length})</h3>
      {pedidos.length === 0 ? (
        <p className="pedido-list-empty">No hay pedidos disponibles</p>
      ) : (
        <ul className="pedido-list-items">
          {pedidos.map((pedido) => (
            <li
              key={pedido.id}
              className={`pedido-item ${selectedId === pedido.id ? 'selected' : ''}`}
              onClick={() => handleSelect(pedido)}
            >
              <div className="pedido-item-header">
                <strong>Pedido #{pedido.id}</strong>
                <span className={`tienda-badge ${pedido.tienda.toLowerCase()}`}>
                  {pedido.tienda}
                </span>
              </div>
              <div className="pedido-item-info">
                <p className="pedido-fecha">
                  <span className="info-icon">📅</span>
                  {pedido.fecha}
                </p>
                {pedido.nodos.length >= 2 ? (
                  <div className="pedido-ruta-info">
                    <p className="ruta-origen">
                      <strong>Origen:</strong>
                      <span className="nodo-value">Nodo {pedido.nodos[0]}</span>
                    </p>
                    <p className="ruta-destino">
                      <strong>Destino:</strong>
                      <span className="nodo-value">Nodo {pedido.nodos[1]}</span>
                    </p>
                  </div>
                ) : (
                  <p>Nodos: {pedido.nodos.length}</p>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

