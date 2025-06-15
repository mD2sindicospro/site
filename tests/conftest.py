import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.mensagem import Mensagem
from app.models.property import Property
from app.models.activity import Activity
from app.models.message import Message
from flask import current_app
import os

@pytest.fixture(scope='function')
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    if os.path.exists('test.db'):
        os.remove('test.db')

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def admin_user(app):
    with app.app_context():
        user = User(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='admin',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user

@pytest.fixture
def normal_user(app):
    with app.app_context():
        user = User(
            name='user',
            email='user@example.com',
            password='user123',
            role='user',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user

@pytest.fixture
def test_property(app, supervisor_user):
    with app.app_context():
        property = Property(
            nome='Test Property',
            endereco='Test Address',
            numero_apartamentos=10,
            supervisor_id=supervisor_user.id
        )
        db.session.add(property)
        db.session.commit()
        return property

@pytest.fixture
def test_activity(app, normal_user, test_property):
    """Fixture para criar uma atividade de teste."""
    activity = Activity(
        title='Test Activity',
        description='Test Description',
        property_id=test_property.id,
        responsible_id=normal_user.id,
        delivery_date='2024-12-31',
        status='pending'
    )
    db.session.add(activity)
    db.session.commit()
    return activity

@pytest.fixture(scope='function')
def test_user(app):
    """Cria um usuário de teste."""
    with app.app_context():
        user = User(
            name='testuser',
            email='test@example.com',
            password='password123',
            role='user',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user

@pytest.fixture(scope='function')
def supervisor_user(app):
    """Cria um usuário supervisor de teste."""
    with app.app_context():
        supervisor = User(
            username='supervisor',
            email='supervisor@example.com',
            password='supervisor123',
            role='supervisor',
            is_active=True
        )
        db.session.add(supervisor)
        db.session.commit()
        db.session.refresh(supervisor)
        return supervisor

@pytest.fixture(scope='function')
def test_category(app):
    """Cria uma categoria de teste."""
    with app.app_context():
        category = Category(
            name='Test Category',
            description='Test Description',
            is_active=True
        )
        db.session.add(category)
        db.session.commit()
        db.session.refresh(category)
        yield category
        db.session.delete(category)
        db.session.commit()

@pytest.fixture(scope='function')
def test_product(app, test_category):
    """Cria um produto de teste."""
    with app.app_context():
        product = Product(
            name='Test Product',
            description='Test Description',
            price=99.99,
            stock=10,
            category_id=test_category.id,
            is_active=True
        )
        db.session.add(product)
        db.session.commit()
        db.session.refresh(product)
        yield product
        db.session.delete(product)
        db.session.commit()

@pytest.fixture(scope='function')
def test_cart(app, test_user):
    """Cria um carrinho de teste."""
    with app.app_context():
        cart = Cart(user_id=test_user.id)
        db.session.add(cart)
        db.session.commit()
        db.session.refresh(cart)
        yield cart
        db.session.delete(cart)
        db.session.commit() 