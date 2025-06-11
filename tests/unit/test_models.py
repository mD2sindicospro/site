import pytest
from app.extensions import db
from app.models.user import User
from app.models.condominio import Condominio
from app.models.atividade import Atividade
from datetime import datetime

def test_create_user(app):
    """Testa a criação de um usuário."""
    user = User(
        username='testuser',
        email='test@example.com',
        password='test123',
        role='user'
    )
    db.session.add(user)
    db.session.commit()
    
    assert user.id is not None
    assert user.username == 'testuser'
    assert user.email == 'test@example.com'
    assert user.role == 'user'
    assert user.is_active is True
    assert user.check_password('test123')
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)

def test_create_user_invalid_data(app):
    """Testa a criação de um usuário com dados inválidos."""
    with pytest.raises(ValueError):
        User(username='', email='test@test.com', password='test123')
    
    with pytest.raises(ValueError):
        User(username='testuser', email='', password='test123')
    
    with pytest.raises(ValueError):
        User(username='testuser', email='test@test.com', password='test123', role='invalid_role')

def test_create_condominio(app):
    """Testa a criação de um condomínio."""
    supervisor = User(
        username='supervisor',
        email='supervisor@test.com',
        password='test123',
        role='supervisor'
    )
    db.session.add(supervisor)
    db.session.commit()

    condominio = Condominio(
        nome='Test Condomínio',
        endereco='Test Address',
        numero_apartamentos=10,
        supervisor_id=supervisor.id
    )
    db.session.add(condominio)
    db.session.commit()

    assert condominio.id is not None
    assert condominio.nome == 'Test Condomínio'
    assert condominio.endereco == 'Test Address'
    assert condominio.numero_apartamentos == 10
    assert condominio.supervisor_id == supervisor.id
    assert isinstance(condominio.created_at, datetime)
    assert isinstance(condominio.updated_at, datetime)

def test_create_condominio_invalid_data(app):
    """Testa a criação de um condomínio com dados inválidos."""
    with pytest.raises(ValueError):
        Condominio(nome='', endereco='Test Address', numero_apartamentos=10)
    
    with pytest.raises(ValueError):
        Condominio(nome='Test Condomínio', endereco='', numero_apartamentos=10)
    
    with pytest.raises(ValueError):
        Condominio(nome='Test Condomínio', endereco='Test Address', numero_apartamentos=-1)

def test_create_atividade(app):
    """Testa a criação de uma atividade."""
    supervisor = User(
        username='supervisor',
        email='supervisor@test.com',
        password='test123',
        role='supervisor'
    )
    db.session.add(supervisor)
    db.session.commit()

    condominio = Condominio(
        nome='Test Condomínio',
        endereco='Test Address',
        numero_apartamentos=10,
        supervisor_id=supervisor.id
    )
    db.session.add(condominio)
    db.session.commit()

    atividade = Atividade(
        titulo='Test Atividade',
        descricao='Test Description',
        condominio_id=condominio.id,
        responsavel_id=supervisor.id,
        data_entrega='2024-12-31',
        status='pendente'
    )
    db.session.add(atividade)
    db.session.commit()

    assert atividade.id is not None
    assert atividade.titulo == 'Test Atividade'
    assert atividade.descricao == 'Test Description'
    assert atividade.condominio_id == condominio.id
    assert atividade.responsavel_id == supervisor.id
    assert atividade.data_entrega == '2024-12-31'
    assert atividade.status == 'pendente'
    assert isinstance(atividade.created_at, datetime)
    assert isinstance(atividade.updated_at, datetime)

def test_create_atividade_invalid_data(app):
    """Testa a criação de uma atividade com dados inválidos."""
    with pytest.raises(ValueError):
        Atividade(titulo='', descricao='Test Description', status='pendente')
    
    with pytest.raises(ValueError):
        Atividade(titulo='Test Atividade', descricao='', status='pendente')
    
    with pytest.raises(ValueError):
        Atividade(titulo='Test Atividade', descricao='Test Description', status='invalid_status')

def test_user_password_hashing(app):
    """Testa o hash de senha do usuário."""
    user = User(
        username='testuser',
        email='test@test.com',
        password='test123'
    )
    assert user.password_hash is not None
    assert user.password_hash != 'test123'
    assert user.check_password('test123')
    assert not user.check_password('wrongpass')

def test_user_password_update(app):
    """Testa a atualização de senha do usuário."""
    user = User(
        username='testuser',
        email='test@test.com',
        password='test123'
    )
    user.set_password('newpass')
    assert user.check_password('newpass')
    assert not user.check_password('test123')

def test_condominio_supervisor_relationship(app):
    """Testa o relacionamento entre condomínio e supervisor."""
    supervisor = User(
        username='supervisor',
        email='supervisor@test.com',
        password='test123',
        role='supervisor'
    )
    db.session.add(supervisor)
    db.session.commit()

    condominio = Condominio(
        nome='Test Condomínio',
        endereco='Test Address',
        numero_apartamentos=10,
        supervisor_id=supervisor.id
    )
    db.session.add(condominio)
    db.session.commit()

    assert condominio.supervisor == supervisor
    assert supervisor.condominios[0] == condominio

def test_atividade_status_update(app):
    """Testa a atualização de status da atividade."""
    atividade = Atividade(
        titulo='Test Atividade',
        descricao='Test Description',
        status='pendente'
    )
    atividade.status = 'em_andamento'
    assert atividade.status == 'em_andamento'

def test_atividade_invalid_status(app):
    """Testa a tentativa de atualização com status inválido."""
    atividade = Atividade(
        titulo='Test Atividade',
        descricao='Test Description',
        status='pendente'
    )
    with pytest.raises(ValueError):
        atividade.status = 'invalid_status'

def test_user_deactivation(app):
    """Testa a desativação de usuário."""
    user = User(
        username='testuser',
        email='test@test.com',
        password='test123'
    )
    assert user.is_active
    user.deactivate()
    assert not user.is_active
    assert user.deactivated_at is not None 