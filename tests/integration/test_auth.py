import pytest
from app.models.user import User
from app.extensions import db

def test_login_success(client, normal_user):
    """Testa o login com credenciais válidas."""
    response = client.post('/auth/login', data={
        'email': 'user@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Bem-vindo' in response.data

def test_login_failure(client):
    """Testa o login com credenciais inválidas."""
    response = client.post('/auth/login', data={
        'email': 'wrong@example.com',
        'password': 'wrongpass'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Email ou senha inv\xc3\xa1lidos' in response.data

def test_logout(client, normal_user):
    """Testa o logout."""
    # Faz login primeiro
    client.post('/auth/login', data={
        'email': 'user@example.com',
        'password': 'password123'
    })
    
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Voc\xc3\xaa foi desconectado' in response.data

@pytest.fixture
def normal_user():
    """Fixture para criar um usuário normal."""
    user = User(
        name='testuser',
        email='user@example.com',
        role='user'
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user 