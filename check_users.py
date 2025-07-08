from app import create_app
from app.models.user import User
from app.extensions import db

app = create_app()
with app.app_context():
    users = User.query.all()
    print(f'Total de usuários: {len(users)}')
    
    for user in users:
        print(f'Email: {user.email}')
        if user.password_hash:
            print(f'Hash: {user.password_hash[:50]}...')
            print(f'Hash length: {len(user.password_hash)}')
        else:
            print('Hash: None')
        print('---') 