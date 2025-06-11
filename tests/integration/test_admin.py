import pytest
from app.models.user import User
from app.extensions import db

def test_admin_dashboard_access(client, admin_user):
    """Testa o acesso ao dashboard administrativo."""
    # Faz login como admin
    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'admin123'
    })
    
    response = client.get('/admin/dashboard')
    assert response.status_code == 200
    assert b'Dashboard Administrativo' in response.data

def test_admin_dashboard_denied(client, normal_user):
    """Testa o acesso negado ao dashboard administrativo."""
    # Faz login como usuário normal
    client.post('/auth/login', data={
        'email': 'user@example.com',
        'password': 'password123'
    })
    
    response = client.get('/admin/dashboard')
    assert response.status_code == 302  # Redireciona para home
    assert b'Acesso negado' in response.data

def test_create_user(client, admin_user):
    """Testa a criação de um novo usuário."""
    # Faz login como admin
    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'admin123'
    })
    
    response = client.post('/admin/user/create', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'newpass123',
        'name': 'New User',
        'role': 'user',
        'is_active': True
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Usu\xc3\xa1rio criado com sucesso' in response.data

def test_edit_user(client, admin_user, normal_user):
    """Testa a edição de um usuário existente."""
    # Faz login como admin
    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'admin123'
    })
    
    response = client.post(f'/admin/user/{normal_user.id}/edit', data={
        'username': 'editeduser',
        'email': 'edited@example.com',
        'name': 'Edited User',
        'role': 'user',
        'is_active': True
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Usu\xc3\xa1rio atualizado com sucesso' in response.data

@pytest.fixture
def admin_user():
    """Fixture para criar um usuário administrador."""
    user = User(
        username='admin',
        email='admin@example.com',
        name='Admin User',
        role='admin'
    )
    user.set_password('admin123')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def normal_user():
    """Fixture para criar um usuário normal."""
    user = User(
        username='testuser',
        email='user@example.com',
        name='Test User',
        role='user'
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user 