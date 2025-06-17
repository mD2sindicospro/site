from app import create_app
from app.extensions import db
from app.models.user import User
import os
import sys
from sqlalchemy import text

def reset_production_database():
    # Verifica se está em ambiente de produção
    if os.getenv('FLASK_ENV') != 'production':
        print('ERRO: Este script só pode ser executado em ambiente de produção!')
        print('Defina a variável de ambiente FLASK_ENV=production antes de executar.')
        sys.exit(1)

    # Confirmação do usuário
    print('ATENÇÃO: Você está prestes a resetar o banco de dados de PRODUÇÃO!')
    print('Todos os dados serão perdidos permanentemente.')
    confirm = input('Digite "RESETAR" para confirmar: ')
    
    if confirm != 'RESETAR':
        print('Operação cancelada.')
        sys.exit(0)

    app = create_app('production')
    
    with app.app_context():
        # Desativa as restrições de chave estrangeira temporariamente
        db.session.execute(text('SET CONSTRAINTS ALL DEFERRED'))
        
        # Dropa todas as tabelas com CASCADE
        db.session.execute(text('DROP SCHEMA public CASCADE'))
        db.session.execute(text('CREATE SCHEMA public'))
        db.session.commit()
        
        # Cria todas as tabelas novamente
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
        
        print('\nBanco de dados de produção resetado com sucesso!')
        print('Usuário admin criado:')
        print('Email: admin@m2d.com')
        print('Senha: admin123')
        print('\nIMPORTANTE: Por segurança, altere a senha do admin após o primeiro login!')

if __name__ == '__main__':
    reset_production_database() 