from app import create_app
from app.models.user import User
from app.extensions import db

app = create_app()
with app.app_context():
    users = User.query.filter_by(password_hash=None).all()
    print(f'Usuários com senha nula: {len(users)}')
    for user in users:
        user.set_password('senha123')
        db.session.add(user)
        print(f'Senha redefinida para: {user.email}')
    db.session.commit()
    print('Senhas redefinidas com sucesso!') 