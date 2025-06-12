from app import create_app
from app.models.user import User
from app.extensions import db
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

def create_admin_user():
    app = create_app()
    with app.app_context():
        if User.query.filter_by(email='admin@admin.com').first():
            print('Usuário já existe!')
            return
        admin = User(
            name='Admin',
            email='admin@admin.com',
            role='admin',
            is_active=True
        )
        admin.set_password('123456')
        db.session.add(admin)
        db.session.commit()
        print('Usuário admin criado com sucesso!')
        print('Email: admin@admin.com')
        print('Senha: 123456')

def create_diego_admin():
    app = create_app()
    with app.app_context():
        if User.query.filter_by(email='diego@md2.com').first():
            print('Usuário Diego já existe!')
            return
        admin = User(
            name='Diego',
            email='diego@md2.com',
            role='admin',
            is_active=True
        )
        admin.set_password('diego123')
        db.session.add(admin)
        db.session.commit()
        print('Usuário administrador Diego criado com sucesso!')
        print('Email: diego@md2.com')
        print('Senha: diego123')

def create_isaac_admin():
    app = create_app()
    with app.app_context():
        if User.query.filter_by(email='isaac@md2.com').first():
            print('Usuário Isaac já existe!')
            return
        admin = User(
            name='Isaac',
            email='isaac@md2.com',
            role='admin',
            is_active=True
        )
        admin.set_password('123456')
        db.session.add(admin)
        db.session.commit()
        print('Usuário administrador Isaac criado com sucesso!')
        print('Email: isaac@md2.com')
        print('Senha: 123456')

if __name__ == '__main__':
    create_admin_user()
    create_diego_admin()
    create_isaac_admin() 