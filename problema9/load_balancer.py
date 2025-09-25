import socket
import threading
import json
from datetime import datetime
from config import Config

class LoadBalancer:
    def __init__(self):
        self.backend_servers = Config.BACKEND_PORTS.copy()
        self.current_server_index = 0
        self.healthy_servers = set(self.backend_servers)
        self.health_check_thread = threading.Thread(target=self._health_check_loop)
        self.health_check_thread.daemon = True
        
    def start(self):
        """Inicia el balanceador de carga"""
        print("Iniciando balanceador de carga...")
        self.health_check_thread.start()
        self._start_load_balancer()
    
    def _start_load_balancer(self):
        """Inicia el servidor del balanceador"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('localhost', Config.LOAD_BALANCER_PORT))
            s.listen(10)
            print(f"Balanceador escuchando en puerto {Config.LOAD_BALANCER_PORT}")
            
            while True:
                conn, addr = s.accept()
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(conn, addr)
                )
                client_thread.daemon = True
                client_thread.start()
    
    def _handle_client(self, conn, addr):
        """Maneja conexiones de clientes"""
        try:
            # Recibir request del cliente
            data = conn.recv(1024).decode('utf-8')
            
            if data:
                # Seleccionar servidor backend usando round-robin
                backend_server = self._select_backend_server()
                
                if backend_server:
                    # Forward request al backend
                    response = self._forward_to_backend(backend_server, data)
                    conn.send(response.encode('utf-8'))
                else:
                    # No hay servidores disponibles
                    error_response = json.dumps({
                        'error': 'No hay servidores backend disponibles',
                        'timestamp': datetime.now().isoformat()
                    })
                    conn.send(error_response.encode('utf-8'))
                    
        except Exception as e:
            print(f"Error manejando cliente: {e}")
            error_response = json.dumps({
                'error': f'Error interno: {str(e)}',
                'timestamp': datetime.now().isoformat()
            })
            conn.send(error_response.encode('utf-8'))
        finally:
            conn.close()
    
    def _select_backend_server(self):
        """Selecciona un servidor backend usando round-robin"""
        if not self.healthy_servers:
            return None
            
        # Round-robin simple
        available_servers = list(self.healthy_servers)
        self.current_server_index = (self.current_server_index + 1) % len(available_servers)
        return available_servers[self.current_server_index]
    
    def _forward_to_backend(self, backend_port, data):
        """Forward request al servidor backend"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect(('localhost', backend_port))
                s.send(data.encode('utf-8'))
                response = s.recv(1024).decode('utf-8')
                return response
        except Exception as e:
            # Marcar servidor como no saludable
            self.healthy_servers.discard(backend_port)
            return json.dumps({
                'error': f'Error conectando con backend: {str(e)}',
                'timestamp': datetime.now().isoformat()
            })
    
    def _health_check_loop(self):
        """Verifica periódicamente la salud de los servidores backend"""
        import time
        while True:
            self._check_all_servers()
            time.sleep(Config.HEALTH_CHECK_INTERVAL)
    
    def _check_all_servers(self):
        """Verifica la salud de todos los servidores"""
        for server_port in self.backend_servers:
            if self._check_server_health(server_port):
                self.healthy_servers.add(server_port)
            else:
                self.healthy_servers.discard(server_port)
    
    def _check_server_health(self, server_port):
        """Verifica la salud de un servidor específico"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(Config.HEALTH_CHECK_TIMEOUT)
                s.connect(('localhost', server_port))
                
                request = json.dumps({'action': 'HEALTH_CHECK'})
                s.send(request.encode('utf-8'))
                
                response = s.recv(1024).decode('utf-8')
                health_data = json.loads(response)
                
                return health_data.get('status') == 'healthy'
                
        except Exception:
            return False