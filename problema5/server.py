import socket
import threading
import os
import struct
from protocol import FileTransferProtocol
from file_handler import FileHandler

class FileServer:
    def __init__(self, host='localhost', port=9000):
        self.host = host
        self.port = port
        self.file_handler = FileHandler('shared_files')
        self.running = False
    
    def start(self):
        """Inicia el servidor"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        
        print(f"Servidor escuchando en {self.host}:{self.port}")
        self.running = True
        
        while self.running:
            try:
                client_socket, address = self.socket.accept()
                print(f"Conexión aceptada de {address}")
                
                # Manejar cliente en hilo separado
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except KeyboardInterrupt:
                print("\nDeteniendo servidor...")
                self.running = False
                break
    
    def handle_client(self, client_socket, address):
        """Maneja la comunicación con un cliente"""
        try:
            while True:
                # Recibir header
                header = client_socket.recv(FileTransferProtocol.HEADER_SIZE)
                if not header:
                    break
                
                command, data_size, checksum = FileTransferProtocol.parse_header(header)
                
                if command == FileTransferProtocol.CMD_UPLOAD:
                    self.handle_upload(client_socket, data_size, checksum)
                elif command == FileTransferProtocol.CMD_DOWNLOAD:
                    self.handle_download(client_socket, data_size)
                elif command == FileTransferProtocol.CMD_LIST:
                    self.handle_list(client_socket)
                elif command == FileTransferProtocol.CMD_END:
                    break
        
        except Exception as e:
            print(f"Error con cliente {address}: {e}")
        finally:
            client_socket.close()
            print(f"Conexión cerrada con {address}")
    
    def handle_upload(self, client_socket, data_size, expected_checksum):
        """Maneja subida de archivos"""
        try:
            # Recibir nombre del archivo
            filename_size = struct.unpack('!I', client_socket.recv(4))[0]
            filename = client_socket.recv(filename_size).decode()
            
            safe_path = self.file_handler.get_safe_path(filename)
            
            # Recibir datos del archivo
            received_data = b''
            bytes_received = 0
            
            while bytes_received < data_size:
                chunk_size = min(FileTransferProtocol.BUFFER_SIZE, data_size - bytes_received)
                chunk = client_socket.recv(chunk_size)
                if not chunk:
                    break
                received_data += chunk
                bytes_received += len(chunk)
            
            # Verificar checksum
            actual_checksum = FileTransferProtocol.calculate_checksum(received_data)
            if actual_checksum != expected_checksum:
                raise ValueError("Checksum no coincide")
            
            # Guardar archivo
            with open(safe_path, 'wb') as f:
                f.write(received_data)
            
            # Enviar confirmación
            ack_header = FileTransferProtocol.create_header(FileTransferProtocol.CMD_ACK)
            client_socket.send(ack_header)
            
            print(f"Archivo {filename} recibido exitosamente")
            
        except Exception as e:
            error_msg = str(e).encode()
            error_header = FileTransferProtocol.create_header(
                FileTransferProtocol.CMD_ERROR, len(error_msg)
            )
            client_socket.send(error_header + error_msg)
    
    def handle_download(self, client_socket, data_size):
        """Maneja descarga de archivos"""
        try:
            # Recibir nombre del archivo
            filename_size = struct.unpack('!I', client_socket.recv(4))[0]
            filename = client_socket.recv(filename_size).decode()
            
            safe_path = self.file_handler.get_safe_path(filename)
            
            if not os.path.exists(safe_path):
                raise FileNotFoundError("Archivo no encontrado")
            
            # Leer archivo y calcular checksum
            with open(safe_path, 'rb') as f:
                file_data = f.read()
            
            checksum = FileTransferProtocol.calculate_checksum(file_data)
            
            # Enviar header con información del archivo
            header = FileTransferProtocol.create_header(
                FileTransferProtocol.CMD_DATA, len(file_data), checksum
            )
            client_socket.send(header)
            
            # Enviar datos del archivo
            bytes_sent = 0
            while bytes_sent < len(file_data):
                chunk = file_data[bytes_sent:bytes_sent + FileTransferProtocol.BUFFER_SIZE]
                client_socket.send(chunk)
                bytes_sent += len(chunk)
            
            print(f"Archivo {filename} enviado exitosamente")
            
        except Exception as e:
            error_msg = str(e).encode()
            error_header = FileTransferProtocol.create_header(
                FileTransferProtocol.CMD_ERROR, len(error_msg)
            )
            client_socket.send(error_header + error_msg)
    
    def handle_list(self, client_socket):
        """Maneja listado de archivos"""
        try:
            files = self.file_handler.list_files()
            file_list = "\n".join(files).encode()
            
            header = FileTransferProtocol.create_header(
                FileTransferProtocol.CMD_DATA, len(file_list)
            )
            client_socket.send(header + file_list)
            
        except Exception as e:
            error_msg = str(e).encode()
            error_header = FileTransferProtocol.create_header(
                FileTransferProtocol.CMD_ERROR, len(error_msg)
            )
            client_socket.send(error_header + error_msg)

if __name__ == "__main__":
    server = FileServer()
    server.start()