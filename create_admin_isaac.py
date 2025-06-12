from app import create_app
from app.models.user import User
from app.extensions import db

def create_admin():
    app = create_app()
    with app.app_context():
        # Verifica se o usuário já existe
        if User.query.filter_by(email='isaac@md2.com').first():
            print('Usuário já existe!')
            return

        # Cria o usuário admin
        admin = User(
            name='Isaac',
            email='isaac@md2.com',
            role='admin',
            is_active=True
        )
        admin.set_password('123456')  # Senha inicial

        # Adiciona ao banco de dados
        db.session.add(admin)
        db.session.commit()
        print('Usuário admin criado com sucesso!')
        print('Email: isaac@md2.com')
        print('Senha: 123456')

if __name__ == '__main__':
    create_admin() 