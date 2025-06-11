from app import create_app
from app.extensions import db
import os
from dotenv import load_dotenv
from pathlib import Path

# Carrega as variáveis de ambiente
load_dotenv()

# Cria diretório de logs se não existir
Path("logs").mkdir(exist_ok=True)

# Determina o ambiente
config_name = os.getenv('FLASK_ENV', 'production')
app = create_app(config_name)

if __name__ == '__main__':
    with app.app_context():
        # Cria as tabelas do banco de dados se não existirem
        db.create_all()
        
        # Configura o host e porta
        host = os.getenv('FLASK_HOST', '127.0.0.1')
        port = int(os.getenv('FLASK_PORT', 5000))
        
        app.run(host=host, port=port) 