from app import create_app
from app.models.user import User
from app.extensions import db
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

def create_admin_user():
    """Cria um usuário administrador"""
    app = create_app('development')
    with app.app_context():
        try:
            # Verifica se já existe um admin
            admin = User.query.filter_by(role='admin').first()
            if admin:
                print("❌ Já existe um usuário administrador!")
                return False

            # Cria o usuário admin
            admin = User(
                username='admin',
                email='admin@example.com',
                password='admin123',
                name='Administrador',
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuário administrador criado com sucesso!")
            print(f"Username: admin")
            print(f"Senha: admin123")
            return True

        except Exception as e:
            print(f"❌ Erro ao criar usuário administrador: {e}")
            return False

if __name__ == '__main__':
    create_admin_user() 