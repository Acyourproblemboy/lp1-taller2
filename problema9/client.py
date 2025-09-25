import socket
import json
import random
import time
from config import Config

class Client:
    def __init__(self, client_id):
        self.client_id = client_id
    
    def send_request(self, action, key=None, value=None):
        """Envía un request al balanceador de carga"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)
                s.connect(('localhost', Config.LOAD_BALANCER_PORT))
                
                request = {
                    'action': action,
                    'key': key,
                    'value': value,
                    'client_id': self.client_id,
                    'timestamp': time.time()
                }
                
                s.send(json.dumps(request).encode('utf-8'))
                response = s.recv(1024).decode('utf-8')
                
                return json.loads(response)
                
        except Exception as e:
            return {'error': str(e)}
    
    def set_data(self, key, value):
        """Envía un comando SET"""
        return self.send_request('SET', key, value)
    
    def get_data(self, key):
        """Envía un comando GET"""
        return self.send_request('GET', key)

def demo_client_usage():
    """Demostración del uso del cliente"""
    client = Client("demo_client")
    
    # Escribir datos
    print("=== Escribiendo datos ===")
    for i in range(5):
        key = f"clave_{i}"
        value = f"valor_{i}_desde_cliente"
        result = client.set_data(key, value)
        print(f"SET {key}: {result}")
        time.sleep(1)
    
    # Leer datos
    print("\n=== Leyendo datos ===")
    for i in range(5):
        key = f"clave_{i}"
        result = client.get_data(key)
        print(f"GET {key}: {result}")
        time.sleep(1)

if __name__ == "__main__":
    demo_client_usage()