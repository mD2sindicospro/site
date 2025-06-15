import pytest
from flask import url_for
from app.models.user import User
from app.models.property import Property
from app.models.activity import Activity

def test_home_page(client):
    """Testa o acesso à página inicial."""
    response = client.get('/')
    assert response.status_code == 302  # Redireciona para login

def test_login_page(client):
    """Testa o acesso à página de login."""
    response = client.get('/auth/login')
    assert response.status_code == 200

def test_login_success(client, test_user):
    """Testa o login com credenciais válidas."""
    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Bem-vindo' in response.data

def test_login_invalid_credentials(client):
    """Testa o login com credenciais inválidas."""
    response = client.post('/auth/login', data={
        'email': 'wrong@example.com',
        'password': 'wrongpass'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Email ou senha inv\xc3\xa1lidos' in response.data

def test_logout(client, test_user):
    """Testa o logout do usuário."""
    # Primeiro faz login
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    # Depois faz logout
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Voc\xc3\xaa foi desconectado' in response.data

def test_property_list(client, supervisor_user, test_property):
    """Testa a listagem de propriedades."""
    # Faz login primeiro
    client.post('/auth/login', data={
        'email': 'supervisor@example.com',
        'password': 'supervisor123'
    })
    
    response = client.get('/property/')
    assert response.status_code == 200
    assert b'Test Property' in response.data

def test_property_create(client, supervisor_user):
    """Testa a criação de uma propriedade."""
    # Faz login primeiro
    client.post('/auth/login', data={
        'email': 'supervisor@example.com',
        'password': 'supervisor123'
    })
    
    response = client.post('/property/create', data={
        'nome': 'New Property',
        'endereco': 'New Address',
        'numero_apartamentos': 20
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Propriedade criada com sucesso' in response.data

def test_activity_list(client, supervisor_user, test_activity):
    """Testa a listagem de atividades."""
    response = client.get('/activity/')
    assert response.status_code == 200
    assert b'Test Activity' in response.data

def test_activity_create(client, supervisor_user, test_property):
    """Testa a criação de uma atividade."""
    response = client.post('/activity/create', data={
        'title': 'Test Activity',
        'description': 'Test Description',
        'property': test_property.id,
        'responsible': supervisor_user.id,
        'delivery_date': '2024-12-31',
        'status': 'pending'
    })
    assert response.status_code == 200
    assert b'Activity created successfully' in response.data

def test_activity_update(client, supervisor_user, test_activity):
    """Testa a atualização de uma atividade."""
    response = client.post(f'/activity/{test_activity.id}/update', data={
        'title': 'Updated Activity',
        'description': 'Updated Description',
        'status': 'in_progress',
        'delivery_date': '2024-12-31'
    })
    assert response.status_code == 200
    assert b'Activity updated successfully' in response.data

def test_unauthorized_access(client):
    """Testa o acesso não autorizado a rotas protegidas."""
    response = client.get('/property/create')
    assert response.status_code == 302  # Redirecionamento para login
    
    response = client.get('/activity/create')
    assert response.status_code == 302  # Redirecionamento para login

def test_admin_only_routes(client, admin_user):
    """Testa o acesso a rotas restritas a administradores."""
    # Faz login como administrador
    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'admin123'
    })
    
    response = client.get('/admin/users')
    assert response.status_code == 200  # Acesso permitido

def test_property_create_page(client, supervisor_user):
    response = client.get('/property/create')
    assert response.status_code == 200 