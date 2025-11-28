import { useState } from 'react';
import MapView from './MapView';
import FilterBar from './FilterBar';
import PedidoList from './PedidoList';
import type { Pedido } from '../../services/api';

export default function AppContainer() {
  const [tiendaFilter, setTiendaFilter] = useState<string>('');
  const [selectedPedido, setSelectedPedido] = useState<Pedido | null>(null);

  const handleFilterChange = (tienda: string) => {
    setTiendaFilter(tienda);
    // Limpiar selección cuando cambia el filtro
    setSelectedPedido(null);
  };

  const handlePedidoSelect = (pedido: Pedido) => {
    setSelectedPedido(pedido);
  };

  return (
    <div className="app-container">
      <div className="map-section">
        <MapView  selectedPedido={selectedPedido} />
      </div>
      <div className="sidebar-section">
        <FilterBar onFilterChange={handleFilterChange} />
        <PedidoList 
          tiendaFilter={tiendaFilter} 
          onPedidoSelect={handlePedidoSelect}
        />
      </div>
    </div>
  );
}

