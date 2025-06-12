import os
import sys
import pytest
from pathlib import Path
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.condominio import Condominio
from app.models.atividade import Atividade
from datetime import datetime

# Adiciona o diretório raiz ao PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# Configura variáveis de ambiente para testes
os.environ['FLASK_ENV'] = 'testing'
os.environ['FLASK_APP'] = 'app'
os.environ['FLASK_DEBUG'] = '0'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test-secret-key'

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(
            email='user@example.com',
            password='password123',
            name='Test User',
            role='user'
        )
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def test_admin(app):
    with app.app_context():
        admin = User(
            username='admin',
            email='admin@example.com',
            password='admin123',
            name='Admin User',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        return admin

@pytest.fixture
def supervisor_user(app):
    with app.app_context():
        supervisor = User(
            username='supervisor',
            email='supervisor@example.com',
            password='supervisor123',
            name='Supervisor User',
            role='supervisor'
        )
        db.session.add(supervisor)
        db.session.commit()
        return supervisor

@pytest.fixture
def test_condominio(app, supervisor_user):
    with app.app_context():
        condominio = Condominio(
            nome='Test Condomínio',
            endereco='Test Address',
            numero_apartamentos=10,
            supervisor_id=supervisor_user.id
        )
        db.session.add(condominio)
        db.session.commit()
        return condominio

@pytest.fixture
def test_atividade(app, test_condominio, supervisor_user):
    with app.app_context():
        atividade = Atividade(
            titulo='Test Atividade',
            descricao='Test Description',
            condominio_id=test_condominio.id,
            responsavel_id=supervisor_user.id,
            data_entrega=datetime.utcnow(),
            status='pendente'
        )
        db.session.add(atividade)
        db.session.commit()
        return atividade 