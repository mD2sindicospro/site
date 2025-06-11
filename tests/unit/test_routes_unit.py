import pytest
from flask import url_for
from app.models.user import User
from app.models.condominio import Condominio
from app.models.atividade import Atividade

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

def test_condominio_list(client, supervisor_user, test_condominio):
    """Testa a listagem de condomínios."""
    # Faz login primeiro
    client.post('/auth/login', data={
        'email': 'supervisor@example.com',
        'password': 'supervisor123'
    })
    
    response = client.get('/condominio/')
    assert response.status_code == 200
    assert b'Test Condominio' in response.data

def test_condominio_create(client, supervisor_user):
    """Testa a criação de um condomínio."""
    # Faz login primeiro
    client.post('/auth/login', data={
        'email': 'supervisor@example.com',
        'password': 'supervisor123'
    })
    
    response = client.post('/condominio/create', data={
        'nome': 'Novo Condomínio',
        'endereco': 'Nova Rua, 123',
        'numero_apartamentos': 20
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Condom\xc3\xadnio criado com sucesso' in response.data

def test_atividade_list(client, supervisor_user, test_atividade):
    """Testa a listagem de atividades."""
    # Faz login primeiro
    client.post('/auth/login', data={
        'email': 'supervisor@example.com',
        'password': 'supervisor123'
    })
    
    response = client.get('/atividade/')
    assert response.status_code == 200
    assert b'Test Atividade' in response.data

def test_atividade_create(client, supervisor_user, test_condominio):
    """Testa a criação de uma atividade."""
    # Faz login primeiro
    client.post('/auth/login', data={
        'email': 'supervisor@example.com',
        'password': 'supervisor123'
    })
    response = client.post('/atividade/create', data={
        'titulo': 'Nova Atividade',
        'descricao': 'Descrição da nova atividade',
        'condominio': test_condominio.id,
        'responsavel': supervisor_user.id,
        'data_entrega': '2024-12-31',
        'status': 'pendente'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Atividade criada com sucesso' in response.data

def test_atividade_update(client, supervisor_user, test_atividade):
    """Testa a atualização de uma atividade."""
    # Faz login primeiro
    client.post('/auth/login', data={
        'email': 'supervisor@example.com',
        'password': 'supervisor123'
    })
    
    response = client.post(f'/atividade/{test_atividade.id}/update', data={
        'status': 'em_andamento',
        'descricao': 'Descrição atualizada'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Atividade atualizada com sucesso' in response.data

def test_unauthorized_access(client):
    """Testa o acesso não autorizado a rotas protegidas."""
    response = client.get('/condominio/create')
    assert response.status_code == 302  # Redirecionamento para login
    
    response = client.get('/atividade/create')
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