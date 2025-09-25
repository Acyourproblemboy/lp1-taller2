import struct
import hashlib
import os

class FileTransferProtocol:
    # Comandos
    CMD_UPLOAD = b'UPLD'
    CMD_DOWNLOAD = b'DOWN'
    CMD_LIST = b'LIST'
    CMD_ACK = b'ACK'
    CMD_ERROR = b'ERR'
    CMD_DATA = b'DATA'
    CMD_END = b'END'
    
    # Tamaño del buffer
    BUFFER_SIZE = 4096
    HEADER_SIZE = 12  # 4 bytes comando + 4 bytes tamaño + 4 bytes checksum
    
    @staticmethod
    def create_header(command, data_size=0, checksum=0):
        """Crea un header para el protocolo"""
        return struct.pack('!4sII', command, data_size, checksum)
    
    @staticmethod
    def parse_header(header):
        """Parsea el header del protocolo"""
        try:
            command, data_size, checksum = struct.unpack('!4sII', header)
            return command, data_size, checksum
        except:
            return None, 0, 0
    
    @staticmethod
    def calculate_checksum(data):
        """Calcula checksum MD5 de los datos"""
        return int(hashlib.md5(data).hexdigest()[:8], 16) & 0xFFFFFFFF
    
    @staticmethod
    def safe_path(base_path, filename):
        """Previene path traversal attacks"""
        # Normaliza el path y asegura que esté dentro del directorio base
        full_path = os.path.abspath(os.path.join(base_path, filename))
        base_path = os.path.abspath(base_path)
        
        if not full_path.startswith(base_path):
            raise ValueError("Intento de acceso a ruta no permitida")
        
        return full_path