import pytest
from flask import url_for
from app.models import User, Property, Activity
from app.models.property import Property as PropertyModel
from app.models.activity import Activity as ActivityModel

def test_login_page(client):
    """Testa a página de login."""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Login' in response.data

def test_login_invalid_credentials(client):
    """Testa login com credenciais inválidas."""
    response = client.post('/auth/login', data={
        'email': 'invalid@example.com',
        'password': 'wrongpassword'
    })
    assert response.status_code == 200
    assert b'Invalid email or password' in response.data

def test_create_activity(client, supervisor_user, test_property):
    """Testa a criação de uma atividade."""
    # Faz login primeiro
    client.post('/auth/login', data={
        'email': 'supervisor@example.com',
        'password': 'supervisor123'
    })

    response = client.post('/activity/create', data={
        'titulo': 'Test Activity',
        'descricao': 'Test Description',
        'property': test_property.id,
        'responsavel': supervisor_user.id,
        'data_entrega': '2024-12-31',
        'status': 'pending'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Activity created successfully' in response.data

def test_property_creation(client, supervisor_user):
    """Testa a criação de uma propriedade."""
    # Faz login primeiro
    client.post('/auth/login', data={
        'email': 'supervisor@example.com',
        'password': 'supervisor123'
    })

    response = client.post('/property/create', data={
        'nome': 'Test Property',
        'endereco': 'Test Address',
        'numero_apartamentos': 20
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Property created successfully' in response.data 