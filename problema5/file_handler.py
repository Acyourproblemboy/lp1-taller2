import os
import hashlib

class FileHandler:
    def __init__(self, base_directory):
        self.base_directory = base_directory
        os.makedirs(base_directory, exist_ok=True)
    
    def list_files(self):
        """Lista todos los archivos en el directorio compartido"""
        try:
            files = []
            for filename in os.listdir(self.base_directory):
                filepath = os.path.join(self.base_directory, filename)
                if os.path.isfile(filepath):
                    size = os.path.getsize(filepath)
                    files.append(f"{filename} ({size} bytes)")
            return files
        except Exception as e:
            return [f"Error al listar archivos: {str(e)}"]
    
    def file_exists(self, filename):
        """Verifica si un archivo existe"""
        safe_path = self.get_safe_path(filename)
        return os.path.exists(safe_path)
    
    def get_safe_path(self, filename):
        """Obtiene una ruta segura para el archivo"""
        # Implementaríamos la validación de seguridad aquí
        return os.path.join(self.base_directory, filename)
    
    def calculate_file_checksum(self, filepath):
        """Calcula el checksum MD5 de un archivo"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()