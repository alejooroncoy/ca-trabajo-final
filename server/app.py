from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from routes import pedidos, rutas, grafo

app = FastAPI(title="Sistema de Gestión de Pedidos", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:4321"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(pedidos.router, prefix="/api/pedidos", tags=["pedidos"])
app.include_router(rutas.router, prefix="/api/rutas", tags=["rutas"])
app.include_router(grafo.router, prefix="/api/grafo", tags=["grafo"])

@app.get("/")
def root():
    return {"message": "Sistema de Gestión de Pedidos API"}

