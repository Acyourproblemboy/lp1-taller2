import socket
import struct
import os
from protocol import FileTransferProtocol

class FileClient:
    def __init__(self, host='localhost', port=9000):
        self.host = host
        self.port = port
        self.socket = None
    
    def connect(self):
        """Conecta al servidor"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        print(f"Conectado al servidor {self.host}:{self.port}")
    
    def disconnect(self):
        """Desconecta del servidor"""
        if self.socket:
            end_header = FileTransferProtocol.create_header(FileTransferProtocol.CMD_END)
            self.socket.send(end_header)
            self.socket.close()
            self.socket = None
            print("Desconectado del servidor")
    
    def upload_file(self, filepath):
        """Sube un archivo al servidor"""
        try:
            if not os.path.exists(filepath):
                print("Archivo no encontrado")
                return False
            
            filename = os.path.basename(filepath)
            
            # Leer archivo y calcular checksum
            with open(filepath, 'rb') as f:
                file_data = f.read()
            
            checksum = FileTransferProtocol.calculate_checksum(file_data)
            
            # Enviar header de upload
            header = FileTransferProtocol.create_header(
                FileTransferProtocol.CMD_UPLOAD, len(file_data), checksum
            )
            self.socket.send(header)
            
            # Enviar nombre del archivo
            filename_encoded = filename.encode()
            self.socket.send(struct.pack('!I', len(filename_encoded)))
            self.socket.send(filename_encoded)
            
            # Enviar datos del archivo
            bytes_sent = 0
            while bytes_sent < len(file_data):
                chunk = file_data[bytes_sent:bytes_sent + FileTransferProtocol.BUFFER_SIZE]
                self.socket.send(chunk)
                bytes_sent += len(chunk)
            
            # Esperar confirmación
            response_header = self.socket.recv(FileTransferProtocol.HEADER_SIZE)
            command, data_size, _ = FileTransferProtocol.parse_header(response_header)
            
            if command == FileTransferProtocol.CMD_ACK:
                print("Archivo subido exitosamente")
                return True
            else:
                error_data = self.socket.recv(data_size)
                print(f"Error: {error_data.decode()}")
                return False
                
        except Exception as e:
            print(f"Error al subir archivo: {e}")
            return False
    
    def download_file(self, filename, save_path):
        """Descarga un archivo del servidor"""
        try:
            # Enviar header de download
            header = FileTransferProtocol.create_header(FileTransferProtocol.CMD_DOWNLOAD)
            self.socket.send(header)
            
            # Enviar nombre del archivo
            filename_encoded = filename.encode()
            self.socket.send(struct.pack('!I', len(filename_encoded)))
            self.socket.send(filename_encoded)
            
            # Recibir respuesta
            response_header = self.socket.recv(FileTransferProtocol.HEADER_SIZE)
            command, data_size, expected_checksum = FileTransferProtocol.parse_header(response_header)
            
            if command == FileTransferProtocol.CMD_ERROR:
                error_data = self.socket.recv(data_size)
                print(f"Error: {error_data.decode()}")
                return False
            
            # Recibir datos del archivo
            received_data = b''
            bytes_received = 0
            
            while bytes_received < data_size:
                chunk_size = min(FileTransferProtocol.BUFFER_SIZE, data_size - bytes_received)
                chunk = self.socket.recv(chunk_size)
                if not chunk:
                    break
                received_data += chunk
                bytes_received += len(chunk)
            
            # Verificar checksum
            actual_checksum = FileTransferProtocol.calculate_checksum(received_data)
            if actual_checksum != expected_checksum:
                print("Error: Checksum no coincide")
                return False
            
            # Guardar archivo
            with open(save_path, 'wb') as f:
                f.write(received_data)
            
            print(f"Archivo descargado exitosamente: {save_path}")
            return True
            
        except Exception as e:
            print(f"Error al descargar archivo: {e}")
            return False
    
    def list_files(self):
        """Lista archivos disponibles en el servidor"""
        try:
            # Enviar comando LIST
            header = FileTransferProtocol.create_header(FileTransferProtocol.CMD_LIST)
            self.socket.send(header)
            
            # Recibir respuesta
            response_header = self.socket.recv(FileTransferProtocol.HEADER_SIZE)
            command, data_size, _ = FileTransferProtocol.parse_header(response_header)
            
            if command == FileTransferProtocol.CMD_ERROR:
                error_data = self.socket.recv(data_size)
                print(f"Error: {error_data.decode()}")
                return False
            
            # Recibir lista de archivos
            file_list_data = self.socket.recv(data_size)
            file_list = file_list_data.decode()
            
            print("\nArchivos disponibles:")
            print(file_list)
            return True
            
        except Exception as e:
            print(f"Error al listar archivos: {e}")
            return False

def main():
    client = FileClient()
    
    try:
        client.connect()
        
        while True:
            print("\nOpciones:")
            print("1. Listar archivos")
            print("2. Subir archivo")
            print("3. Descargar archivo")
            print("4. Salir")
            
            choice = input("Selecciona una opción: ")
            
            if choice == '1':
                client.list_files()
                
            elif choice == '2':
                filepath = input("Ruta del archivo a subir: ")
                if os.path.exists(filepath):
                    client.upload_file(filepath)
                else:
                    print("Archivo no encontrado")
                    
            elif choice == '3':
                filename = input("Nombre del archivo a descargar: ")
                save_path = input("Ruta donde guardar: ")
                client.download_file(filename, save_path)
                
            elif choice == '4':
                break
                
            else:
                print("Opción no válida")
                
    except KeyboardInterrupt:
        print("\nSaliendo...")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()