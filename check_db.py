from app import create_app
from app.extensions import db
import os
from dotenv import load_dotenv
from sqlalchemy import inspect

# Carrega as variáveis de ambiente
load_dotenv()

def check_database_connection():
    """Verifica a conexão com o banco de dados"""
    app = create_app('development')
    with app.app_context():
        try:
            # Tenta conectar ao banco de dados
            db.engine.connect()
            print("✅ Conexão com o banco de dados estabelecida com sucesso!")
            
            # Verifica se as tabelas existem usando o inspector
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print("\nTabelas encontradas:")
            for table in tables:
                print(f"- {table}")
                
        except Exception as e:
            print(f"❌ Erro ao conectar com o banco de dados: {e}")
            return False
        return True

if __name__ == '__main__':
    check_database_connection() 