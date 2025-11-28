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
    <div className="mb-8 pb-6 border-b border-blue-primary/10">
      <label htmlFor="tienda-filter" className="flex items-center gap-2 mb-3 font-semibold text-sm text-blue-dark uppercase tracking-wide">
        <span>🔍</span>
        Filtrar por tienda
      </label>
      <select
        id="tienda-filter"
        value={tienda}
        onChange={handleChange}
        className="w-full px-4 py-3 border border-blue-primary/20 rounded-lg text-sm bg-white text-blue-dark font-medium transition-all duration-300 hover:border-blue-primary/40 focus:outline-none focus:ring-2 focus:ring-blue-primary/20 focus:border-blue-primary cursor-pointer"
      >
        <option value="">Todas las tiendas</option>
        <option value="Saga">Saga</option>
        <option value="Ripley">Ripley</option>
      </select>
    </div>
  );
}

