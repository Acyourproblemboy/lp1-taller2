import socket
import threading
import time
import json
from datetime import datetime
from config import Config

class BackendServer:
    def __init__(self, server_id, port, other_servers):
        self.server_id = server_id
        self.port = port
        self.other_servers = other_servers  # Lista de puertos de otros servidores
        self.data = Config.load_data(server_id)
        self.is_healthy = True
        self.health_checks = {}  # Estado de otros servidores
        self.sync_lock = threading.Lock()
        
    def start(self):
        """Inicia el servidor backend"""
        # Hilo principal para recibir requests
        server_thread = threading.Thread(target=self._start_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Hilo para health checks
        health_thread = threading.Thread(target=self._health_check_loop)
        health_thread.daemon = True
        health_thread.start()
        
        # Hilo para sincronización
        sync_thread = threading.Thread(target=self._sync_loop)
        sync_thread.daemon = True
        sync_thread.start()
        
        print(f"Servidor {self.server_id} iniciado en puerto {self.port}")
        
    def _start_server(self):
        """Inicia el socket del servidor"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('localhost', self.port))
            s.listen(5)
            
            while True:
                conn, addr = s.accept()
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(conn, addr)
                )
                client_thread.daemon = True
                client_thread.start()
    
    def _handle_client(self, conn, addr):
        """Maneja requests de clientes"""
        try:
            data = conn.recv(1024).decode('utf-8')
            if data:
                response = self._process_request(data)
                conn.send(response.encode('utf-8'))
        except Exception as e:
            print(f"Error manejando cliente: {e}")
        finally:
            conn.close()
    
    def _process_request(self, data):
        """Procesa diferentes tipos de requests"""
        try:
            request = json.loads(data)
            action = request.get('action')
            
            if action == 'GET':
                key = request.get('key')
                return self._get_data(key)
            elif action == 'SET':
                key = request.get('key')
                value = request.get('value')
                return self._set_data(key, value)
            elif action == 'HEALTH_CHECK':
                return self._health_check_response()
            elif action == 'SYNC_DATA':
                return self._sync_data(request.get('data'))
            else:
                return json.dumps({'error': 'Acción no válida'})
                
        except json.JSONDecodeError:
            return json.dumps({'error': 'JSON inválido'})
    
    def _get_data(self, key):
        """Obtiene datos del almacenamiento"""
        with self.sync_lock:
            value = self.data.get(key, 'No encontrado')
            return json.dumps({
                'server_id': self.server_id,
                'key': key,
                'value': value,
                'timestamp': datetime.now().isoformat()
            })
    
    def _set_data(self, key, value):
        """Establece datos en el almacenamiento"""
        with self.sync_lock:
            self.data[key] = {
                'value': value,
                'timestamp': datetime.now().isoformat(),
                'server_id': self.server_id
            }
            Config.save_data(self.server_id, self.data)
            
            return json.dumps({
                'server_id': self.server_id,
                'status': 'OK',
                'key': key,
                'timestamp': datetime.now().isoformat()
            })
    
    def _health_check_response(self):
        """Responde a health checks"""
        return json.dumps({
            'server_id': self.server_id,
            'status': 'healthy' if self.is_healthy else 'unhealthy',
            'timestamp': datetime.now().isoformat()
        })
    
    def _sync_data(self, incoming_data):
        """Sincroniza datos recibidos de otro servidor"""
        with self.sync_lock:
            for key, value in incoming_data.items():
                # Mantener el dato más reciente
                current_timestamp = self.data.get(key, {}).get('timestamp', '')
                incoming_timestamp = value.get('timestamp', '')
                
                if incoming_timestamp > current_timestamp:
                    self.data[key] = value
            
            Config.save_data(self.server_id, self.data)
            return json.dumps({'status': 'sync_ok'})
    
    def _health_check_loop(self):
        """Loop para verificar salud de otros servidores"""
        while True:
            for server_port in self.other_servers:
                if server_port != self.port:  # No verificar a sí mismo
                    self._check_server_health(server_port)
            time.sleep(Config.HEALTH_CHECK_INTERVAL)
    
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
                
                self.health_checks[server_port] = {
                    'status': health_data.get('status', 'unknown'),
                    'last_check': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.health_checks[server_port] = {
                'status': 'unhealthy',
                'last_check': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _sync_loop(self):
        """Loop para sincronizar datos entre servidores"""
        while True:
            time.sleep(Config.SYNC_INTERVAL)
            self._sync_with_other_servers()
    
    def _sync_with_other_servers(self):
        """Sincroniza datos con otros servidores saludables"""
        healthy_servers = [
            port for port, status in self.health_checks.items() 
            if status.get('status') == 'healthy'
        ]
        
        for server_port in healthy_servers:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5)
                    s.connect(('localhost', server_port))
                    
                    request = json.dumps({
                        'action': 'SYNC_DATA',
                        'data': self.data
                    })
                    s.send(request.encode('utf-8'))
                    
                    # Esperar respuesta (aunque no es crítico)
                    s.recv(1024)
                    
            except Exception as e:
                print(f"Error sincronizando con servidor {server_port}: {e}")