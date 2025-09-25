import json
import time

class Config:
    # Configuración de puertos y direcciones
    LOAD_BALANCER_PORT = 8000
    BACKEND_PORTS = [8001, 8002, 8003]
    SYNC_PORT = 9000
    
    # Configuración de health checks
    HEALTH_CHECK_INTERVAL = 5  # segundos
    HEALTH_CHECK_TIMEOUT = 3   # segundos
    
    # Configuración de replicación
    SYNC_INTERVAL = 10  # segundos
    
    @staticmethod
    def save_data(server_id, data):
        """Guarda datos en archivo JSON"""
        filename = f"server_{server_id}_data.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def load_data(server_id):
        """Carga datos desde archivo JSON"""
        filename = f"server_{server_id}_data.json"
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}