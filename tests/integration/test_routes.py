import pytest
from flask import url_for
from app.models import User, Condominio, Atividade
from app.models.atividade import Atividade as AtividadeModel
from app.models.condominio import Condominio as CondominioModel
from app.models.user import User as UserModel
from app.extensions import db

def test_home_page(client):
    """Testa a página inicial."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Sistema de Gest\xc3\xa3o de Condom\xc3\xadnios' in response.data

def test_login_page(client):
    """Testa a página de login."""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Login' in response.data

def test_login_success(client):
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
    assert b'Email ou senha invalidos' in response.data

def test_create_atividade(client, supervisor_user, test_condominio):
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

def test_concluir_atividade(client, supervisor_user, test_atividade):
    """Testa a conclusão de uma atividade."""
    # Faz login primeiro
    client.post('/auth/login', data={
        'email': 'supervisor@example.com',
        'password': 'supervisor123'
    })

    response = client.post(f'/atividade/{test_atividade.id}/concluir', follow_redirects=True)
    assert response.status_code == 200
    assert b'Atividade conclu\xc3\xadda com sucesso' in response.data

def test_condominio_creation(client, supervisor_user):
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