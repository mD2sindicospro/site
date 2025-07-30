import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
import io

class ImageHandler:
    """Classe para gerenciar uploads de imagens"""
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    UPLOAD_FOLDER = 'app/static/uploads/logos'
    
    @staticmethod
    def allowed_file(filename):
        """Verifica se a extensão do arquivo é permitida"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ImageHandler.ALLOWED_EXTENSIONS
    
    @staticmethod
    def create_upload_folder():
        """Cria a pasta de upload se não existir"""
        if not os.path.exists(ImageHandler.UPLOAD_FOLDER):
            os.makedirs(ImageHandler.UPLOAD_FOLDER, exist_ok=True)
    
    @staticmethod
    def save_logo(file, property_id):
        """Salva a logo de um condomínio"""
        if file is None or file.filename == '':
            return None
        
        # Verifica se o arquivo é permitido
        if not ImageHandler.allowed_file(file.filename):
            raise ValueError("Tipo de arquivo não permitido. Use apenas PNG, JPG, JPEG, GIF ou WEBP.")
        
        # Verifica o tamanho do arquivo
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > ImageHandler.MAX_FILE_SIZE:
            raise ValueError("Arquivo muito grande. Tamanho máximo: 5MB.")
        
        # Cria a pasta de upload se não existir
        ImageHandler.create_upload_folder()
        
        # Gera nome único para o arquivo
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"logo_{property_id}_{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(ImageHandler.UPLOAD_FOLDER, unique_filename)
        
        try:
            # Abre a imagem com PIL para validação e otimização
            image = Image.open(file.stream)
            
            # Converte para RGB se necessário
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Redimensiona se a imagem for muito grande
            max_size = (800, 800)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Salva a imagem otimizada
            image.save(file_path, quality=85, optimize=True)
            
            return unique_filename
            
        except Exception as e:
            # Remove o arquivo se houver erro
            if os.path.exists(file_path):
                os.remove(file_path)
            raise ValueError(f"Erro ao processar imagem: {str(e)}")
    
    @staticmethod
    def delete_logo(filename):
        """Remove a logo de um condomínio"""
        if filename:
            file_path = os.path.join(ImageHandler.UPLOAD_FOLDER, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
    
    @staticmethod
    def get_logo_url(filename):
        """Retorna a URL da logo"""
        if filename:
            return f"/static/uploads/logos/{filename}"
        return None
    
    @staticmethod
    def validate_image(file):
        """Valida se o arquivo é uma imagem válida"""
        if file is None or file.filename == '':
            return True, None
        
        # Verifica extensão
        if not ImageHandler.allowed_file(file.filename):
            return False, "Tipo de arquivo não permitido. Use apenas PNG, JPG, JPEG, GIF ou WEBP."
        
        # Verifica tamanho
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > ImageHandler.MAX_FILE_SIZE:
            return False, "Arquivo muito grande. Tamanho máximo: 5MB."
        
        # Verifica se é uma imagem válida
        try:
            image = Image.open(file.stream)
            image.verify()
            file.seek(0)  # Reset do cursor
            return True, None
        except Exception:
            return False, "Arquivo não é uma imagem válida." 