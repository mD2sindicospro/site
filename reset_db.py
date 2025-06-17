from app import create_app
from app.extensions import db
from app.models.user import User
import os

def reset_database():
    app = create_app('development')
    
    with app.app_context():
        # Remove o banco de dados existente
        if os.path.exists('dev.db'):
            os.remove('dev.db')
        
        # Cria todas as tabelas
        db.create_all()
        
        # Cria usuário admin
        admin = User(
            email='admin@m2d.com',
            name='Administrador',
            role='admin',
            password='admin123'
        )
        
        # Adiciona o admin ao banco
        db.session.add(admin)
        db.session.commit()
        
        print('Banco de dados resetado com sucesso!')
        print('Usuário admin criado:')
        print('Email: admin@m2d.com')
        print('Senha: admin123')

if __name__ == '__main__':
    reset_database() 