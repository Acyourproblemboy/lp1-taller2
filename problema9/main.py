import threading
import time
from backend_server import BackendServer
from load_balancer import LoadBalancer
from config import Config

def start_backend_servers():
    """Inicia todos los servidores backend"""
    servers = []
    
    for i, port in enumerate(Config.BACKEND_PORTS):
        # Lista de otros servidores (excluyendo el actual)
        other_servers = [p for p in Config.BACKEND_PORTS if p != port]
        
        server = BackendServer(
            server_id=f"server_{i+1}", 
            port=port, 
            other_servers=other_servers
        )
        
        server_thread = threading.Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        
        servers.append(server)
        print(f"Servidor backend {i+1} configurado en puerto {port}")
    
    return servers

def main():
    """Función principal"""
    print("=== Iniciando Sistema Distribuido ===")
    
    # Iniciar servidores backend
    servers = start_backend_servers()
    
    # Esperar un poco para que los servidores se inicien
    time.sleep(2)
    
    # Iniciar balanceador de carga
    load_balancer = LoadBalancer()
    load_balancer.start()
    
    # Mantener el programa corriendo
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n=== Cerrando sistema ===")

if __name__ == "__main__":
    main()