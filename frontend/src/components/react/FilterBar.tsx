import { useState } from 'react';

interface FilterBarProps {
  onFilterChange: (tienda: string) => void;
}

export default function FilterBar({ onFilterChange }: FilterBarProps) {
  const [tienda, setTienda] = useState<string>('');

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setTienda(value);
    onFilterChange(value);
  };

  return (
    <div className="filter-bar">
      <label htmlFor="tienda-filter">
        <span className="filter-label-icon">🔍</span>
        Filtrar por tienda
      </label>
      <select
        id="tienda-filter"
        value={tienda}
        onChange={handleChange}
        className="filter-select"
      >
        <option value="">Todas las tiendas</option>
        <option value="Saga">Saga</option>
        <option value="Ripley">Ripley</option>
      </select>
    </div>
  );
}

