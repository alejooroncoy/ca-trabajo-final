# Sistema de Gestión de Pedidos con Mapas

Sistema full-stack para gestionar pedidos de entrega, calcular rutas optimizadas usando algoritmos Dijkstra y TSP, y visualizarlas en OpenStreetMap.

## Arquitectura

- **Backend**: FastAPI (Python)
- **Frontend**: React.js con Vite
- **Mapas**: OpenStreetMap con react-leaflet
- **Algoritmos**: Dijkstra y TSP (Traveling Salesman Problem)

## Estructura del Proyecto

```
ca-trabajo-final/
├── server/          # Backend FastAPI
│   ├── app.py       # Aplicación principal
│   ├── main.py      # Modelo Graph existente
│   ├── models/      # Modelos Pydantic
│   ├── repository/  # Patrón Repository
│   ├── services/    # Lógica de negocio
│   ├── algorithms/  # Dijkstra y TSP
│   └── routes/      # Endpoints API
└── frontend/        # Frontend React
    ├── src/
    │   ├── components/  # Componentes React
    │   ├── services/  # Cliente API
    │   └── hooks/     # Hooks personalizados
```

## Instalación

### Backend

1. Navegar al directorio del servidor:
```bash
cd server
```

2. Crear el entorno virtual (si no existe):
```bash
python -m venv venv
```

3. Activar el entorno virtual:
```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows CMD
venv\Scripts\activate.bat

# Linux/Mac
source venv/bin/activate
```

**Nota para Windows PowerShell**: Si obtienes un error de política de ejecución, ejecuta primero:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

4. Instalar dependencias:
```bash
pip install -r requirements.txt
```

5. Iniciar el servidor:
```bash
uvicorn app:app --reload --port 8000
```

El servidor estará disponible en `http://localhost:8000`

### Frontend

1. Navegar al directorio del frontend:
```bash
cd frontend
```

2. Instalar dependencias:
```bash
npm install
```

3. Iniciar el servidor de desarrollo:
```bash
npm run dev
```

El frontend estará disponible en `http://localhost:3000`

## Uso

1. Iniciar el backend (puerto 8000)
2. Iniciar el frontend (puerto 3000)
3. (Opcional) Crear pedidos de ejemplo:
   ```bash
   cd server
   python ejemplo_pedidos.py
   ```
4. Abrir el navegador en `http://localhost:3000`
5. El mapa mostrará todos los nodos del sistema vial
6. Usar el filtro para ver pedidos por tienda (Saga/Ripley)
7. Seleccionar un pedido para calcular y visualizar su ruta optimizada

## API Endpoints

### Pedidos
- `GET /api/pedidos` - Listar pedidos (filtro opcional: `?tienda=Saga`)
- `GET /api/pedidos/{id}` - Obtener pedido
- `POST /api/pedidos` - Crear pedido
- `PUT /api/pedidos/{id}` - Actualizar pedido
- `DELETE /api/pedidos/{id}` - Eliminar pedido

### Rutas
- `POST /api/rutas/calcular` - Calcular ruta optimizada
- `GET /api/rutas/pedido/{id}` - Obtener ruta de un pedido

### Grafo
- `GET /api/grafo/nodos` - Obtener todos los nodos
- `GET /api/grafo/aristas` - Obtener todas las conexiones

## Características

- ✅ Visualización de nodos en OpenStreetMap
- ✅ Cálculo de rutas optimizadas con TSP
- ✅ Filtrado de pedidos por tienda
- ✅ Algoritmo Dijkstra para distancias mínimas
- ✅ Algoritmo TSP con heurística Nearest Neighbor + 2-opt
- ✅ Patrón Repository para gestión de datos
- ✅ Componentes React reutilizables
- ✅ Layout responsive: mapa 70% / sidebar 30%

## Tecnologías

### Backend
- FastAPI
- Pydantic
- Uvicorn

### Frontend
- React 18
- Vite
- react-leaflet
- Axios

