import pytest
from app.models.user import User
from app.extensions import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError

@pytest.fixture(autouse=True)
def setup_database(app):
    """Configura o banco de dados para os testes"""
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()

def test_create_user(app):
    """Testa a criação de um usuário"""
    with app.app_context():
        user = User(
            name='testuser',
            email='test@example.com',
            password='password123',
            role='user'
        )
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.name == 'testuser'
        assert user.email == 'test@example.com'
        assert user.role == 'user'
        assert user.is_active is True
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

def test_user_password_hashing(app):
    """Testa o hash de senha"""
    with app.app_context():
        user = User(
            name='testuser',
            email='test@example.com',
            password='password123'
        )
        
        assert user.password_hash != 'password123'
        assert user.check_password('password123') is True
        assert user.check_password('wrongpassword') is False

def test_user_validation(app):
    """Testa as validações do modelo"""
    with app.app_context():
        # Teste de email inválido
        with pytest.raises(ValueError):
            User(
                name='testuser',
                email='invalid-email',
                password='password123'
            )

        # Teste de username duplicado
        user1 = User(
            name='testuser1',
            email='test1@example.com',
            password='password123'
        )
        db.session.add(user1)
        db.session.commit()

        with pytest.raises(IntegrityError):
            user2 = User(
                name='testuser1',
                email='test2@example.com',
                password='password123'
            )
            db.session.add(user2)
            db.session.commit()

def test_user_update(app):
    """Testa a atualização de usuário"""
    with app.app_context():
        user = User(
            name='testuser',
            email='test@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()

        user.name = 'Updated Name'
        user.email = 'updated@example.com'
        db.session.commit()

        updated_user = User.query.get(user.id)
        assert updated_user.name == 'Updated Name'
        assert updated_user.email == 'updated@example.com'

def test_user_deactivation(app):
    """Testa a desativação de usuário"""
    with app.app_context():
        user = User(
            name='testuser',
            email='test@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()

        user.deactivate()
        db.session.commit()

        deactivated_user = User.query.get(user.id)
        assert deactivated_user.is_active is False
        assert deactivated_user.deactivated_at is not None 