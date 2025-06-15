import pytest
from app.extensions import db
from app.models.user import User
from app.models.property import Property
from app.models.activity import Activity
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

def test_create_property(app):
    with app.app_context():
        supervisor = User(
            username='supervisor',
            email='supervisor@test.com',
            role='supervisor'
        )
        db.session.add(supervisor)
        db.session.commit()

        property = Property(
            name='Test Property',
            address='Test Address',
            numero_apartamentos=10,
            supervisor_id=supervisor.id
        )
        db.session.add(property)
        db.session.commit()

        assert property.id is not None
        assert property.name == 'Test Property'
        assert property.address == 'Test Address'
        assert property.numero_apartamentos == 10
        assert property.supervisor_id == supervisor.id
        assert isinstance(property.created_at, datetime)
        assert isinstance(property.updated_at, datetime)

def test_create_property_invalid_data(app):
    with app.app_context():
        with pytest.raises(ValueError):
            Property(name='', address='Test Address', numero_apartamentos=10)
        
        with pytest.raises(ValueError):
            Property(name='Test Property', address='', numero_apartamentos=10)
        
        with pytest.raises(ValueError):
            Property(name='Test Property', address='Test Address', numero_apartamentos=-1)

def test_create_activity(app):
    """Testa a criação de uma atividade."""
    with app.app_context():
        # Criar usuário supervisor
        supervisor = User(
            username='test_supervisor',
            email='supervisor@test.com',
            role='supervisor'
        )
        db.session.add(supervisor)
        db.session.commit()

        # Criar propriedade
        property = Property(
            name='Test Property',
            address='Test Address'
        )
        db.session.add(property)
        db.session.commit()

        # Criar atividade
        activity = Activity(
            title='Test Activity',
            description='Test Description',
            property_id=property.id,
            responsible_id=supervisor.id,
            delivery_date='2024-12-31',
            status='pending'
        )
        db.session.add(activity)
        db.session.commit()

        # Verificar se a atividade foi criada corretamente
        assert activity.id is not None
        assert activity.title == 'Test Activity'
        assert activity.description == 'Test Description'
        assert activity.property_id == property.id
        assert activity.responsible_id == supervisor.id
        assert activity.delivery_date == '2024-12-31'
        assert activity.status == 'pending'
        assert isinstance(activity.created_at, datetime)
        assert isinstance(activity.updated_at, datetime)

def test_create_activity_invalid_data(app):
    """Testa a criação de uma atividade com dados inválidos."""
    with app.app_context():
        with pytest.raises(ValueError):
            Activity(title='', description='Test Description', status='pending')
        
        with pytest.raises(ValueError):
            Activity(title='Test Activity', description='', status='pending')
        
        with pytest.raises(ValueError):
            Activity(title='Test Activity', description='Test Description', status='invalid_status')

def test_activity_status_update(app):
    """Testa a atualização de status da atividade."""
    with app.app_context():
        activity = Activity(
            title='Test Activity',
            description='Test Description',
            status='pending'
        )
        activity.status = 'in_progress'
        assert activity.status == 'in_progress'

def test_activity_invalid_status(app):
    """Testa a tentativa de atualização com status inválido."""
    with app.app_context():
        activity = Activity(
            title='Test Activity',
            description='Test Description',
            status='pending'
        )
        with pytest.raises(ValueError):
            activity.status = 'invalid_status'

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

def test_property_supervisor_relationship(app):
    with app.app_context():
        supervisor = User(
            username='supervisor',
            email='supervisor@test.com',
            role='supervisor'
        )
        db.session.add(supervisor)
        db.session.commit()

        property = Property(
            name='Test Property',
            address='Test Address',
            numero_apartamentos=10,
            supervisor_id=supervisor.id
        )
        db.session.add(property)
        db.session.commit()

        assert property.supervisor == supervisor
        assert supervisor.properties[0] == property

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