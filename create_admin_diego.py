from app import create_app
from app.models.user import User
from app.extensions import db

def create_admin():
    app = create_app()
    with app.app_context():
        if User.query.filter_by(email='diego@md2.com').first():
            print('Usuário já existe!')
            return
        admin = User(
            name='Diego',
            email='diego@md2.com',
            role='admin',
            is_active=True
        )
        admin.set_password('123456')
        db.session.add(admin)
        db.session.commit()
        print('Usuário admin criado com sucesso!')
        print('Email: diego@md2.com')
        print('Senha: 123456')

if __name__ == '__main__':
    create_admin() 