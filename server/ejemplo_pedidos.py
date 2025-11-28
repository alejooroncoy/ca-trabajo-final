"""
Script de ejemplo para crear pedidos de prueba
Ejecutar después de iniciar el servidor: python ejemplo_pedidos.py
"""
import requests
import json
from datetime import date, timedelta

API_BASE = "http://localhost:8000/api"

def crear_pedido(tienda, fecha, nodos):
    """Crea un pedido en el sistema"""
    response = requests.post(
        f"{API_BASE}/pedidos",
        json={
            "tienda": tienda,
            "fecha": fecha.isoformat(),
            "nodos": nodos
        }
    )
    if response.status_code == 201:
        print(f"✅ Pedido creado: {response.json()}")
        return response.json()
    else:
        print(f"❌ Error creando pedido: {response.text}")
        return None

def main():
    """Crea algunos pedidos de ejemplo"""
    print("Creando pedidos de ejemplo...\n")
    
    hoy = date.today()
    
    # Pedido 1: Saga con 3 nodos
    crear_pedido("Saga", hoy, [0, 5, 10])
    
    # Pedido 2: Ripley con 4 nodos
    crear_pedido("Ripley", hoy + timedelta(days=1), [1, 3, 7, 12])
    
    # Pedido 3: Saga con 5 nodos
    crear_pedido("Saga", hoy + timedelta(days=2), [2, 4, 6, 8, 15])
    
    # Pedido 4: Ripley con 2 nodos
    crear_pedido("Ripley", hoy, [9, 11])
    
    print("\n✅ Pedidos de ejemplo creados!")
    print("\nPuedes verificar los pedidos en:")
    print(f"  GET {API_BASE}/pedidos")
    print(f"  GET {API_BASE}/pedidos?tienda=Saga")
    print(f"  GET {API_BASE}/pedidos?tienda=Ripley")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al servidor.")
        print("   Asegúrate de que el servidor esté ejecutándose en http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

