import socket
import threading

BUFFER_SIZE = 8192

def log(msg):
    print(msg)

def handle_client(client_socket):
    request = client_socket.recv(BUFFER_SIZE).decode('utf-8', errors='ignore')
    
    # Extraer la primera línea
    first_line = request.split('\n')[0]
    log(f"[REQ] {first_line.strip()}")
    
    # Obtener método y destino
    method, path, _ = first_line.split()
    
    if method.upper() == 'CONNECT':
        handle_https_tunnel(client_socket, path)
    else:
        handle_http_request(client_socket, method, path, request)

def handle_https_tunnel(client_socket, path):
    host, port = path.split(':')
    port = int(port)
    
    try:
        remote_socket = socket.create_connection((host, port))
        client_socket.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
        
        # Redirige datos bidireccionalmente
        tunnel(client_socket, remote_socket)
    except Exception as e:
        log(f"[ERROR HTTPS] {e}")
        client_socket.close()

def handle_http_request(client_socket, method, path, original_request):
    try:
        # Parsear host
        host = ""
        lines = original_request.split('\n')
        for line in lines:
            if line.lower().startswith("host:"):
                host = line.split(":")[1].strip()
                break
        
        port = 80
        remote_socket = socket.create_connection((host, port))
        
        # Modificar headers si quieres
        modified_request = original_request.replace("Proxy-Connection", "Connection")
        
        remote_socket.sendall(modified_request.encode('utf-8'))
        while True:
            data = remote_socket.recv(BUFFER_SIZE)
            if not data:
                break
            client_socket.sendall(data)
        
    except Exception as e:
        log(f"[ERROR HTTP] {e}")
    finally:
        client_socket.close()

def tunnel(sock1, sock2):
    def forward(source, dest):
        try:
            while True:
                data = source.recv(BUFFER_SIZE)
                if not data:
                    break
                dest.sendall(data)
        finally:
            source.close()
            dest.close()
    
    threading.Thread(target=forward, args=(sock1, sock2)).start()
    threading.Thread(target=forward, args=(sock2, sock1)).start()

def start_proxy(host='localhost', port=9000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(100)
    log(f"[+] Proxy escuchando en {host}:{port}")
    
    while True:
        client_socket, addr = server.accept()
        log(f"[+] Nueva conexión de {addr}")
        threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()

if __name__ == "__main__":
    start_proxy()
