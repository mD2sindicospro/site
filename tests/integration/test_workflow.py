import pytest
from app.models.user import User
from app.models.property import Property
from app.models.activity import Activity
from app.extensions import db

def test_complete_workflow(client, test_user, test_admin):
    """Testa um fluxo completo de criação e gerenciamento de atividades."""
    # 1. Login como admin
    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'admin123'
    })
    
    # 2. Criar uma nova propriedade
    response = client.post('/property/create', data={
        'nome': 'Test Property',
        'endereco': 'Test Address',
        'numero_apartamentos': 50
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Property created successfully' in response.data
    
    # 3. Buscar o ID da propriedade criada
    property = Property.query.filter_by(nome='Test Property').first()
    assert property is not None
    
    # 4. Criar uma nova atividade
    response = client.post('/activity/create', data={
        'titulo': 'Test Activity',
        'descricao': 'Test activity description',
        'property': property.id,
        'responsavel': test_user.id,
        'data_entrega': '2024-12-31',
        'status': 'pending'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Activity created successfully' in response.data
    
    # 5. Logout como admin
    client.get('/auth/logout')
    
    # 6. Login como usuário normal
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    # 7. Verificar se a atividade está visível
    response = client.get('/activity/')
    assert response.status_code == 200
    assert b'Elevator Maintenance' in response.data
    
    # 8. Atualizar o status da atividade
    activity = Activity.query.filter_by(title='Elevator Maintenance').first()
    response = client.post(f'/activity/{activity.id}/update', data={
        'status': 'in_progress',
        'descricao': 'Updated description'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Activity updated successfully' in response.data
    
    # 9. Finalizar a atividade
    response = client.post(f'/activity/{activity.id}/update', data={
        'status': 'completed',
        'descricao': 'Elevator checked and working normally'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Activity updated successfully' in response.data

def test_user_management_workflow(client, test_admin):
    """Testa o fluxo de gerenciamento de usuários."""
    # 1. Login como admin
    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'admin123'
    })
    
    # 2. Criar novo usuário
    response = client.post('/admin/user/create', data={
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'password123',
        'role': 'user'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'User created successfully' in response.data
    
    # 3. Verificar se o usuário foi criado
    user = User.query.filter_by(email='new@example.com').first()
    assert user is not None
    assert user.username == 'newuser'
    
    # 4. Editar usuário
    response = client.post('/admin/user/2/edit', data={
        'username': 'editeduser',
        'email': 'edited@example.com',
        'role': 'user',
        'is_active': True
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'User updated successfully' in response.data
    
    # 5. Verificar alterações
    user = User.query.filter_by(email='new@example.com').first()
    assert user.username == 'editeduser'
    assert user.role == 'user'
    
    # 6. Desativar usuário
    response = client.post('/admin/user/2/deactivate', follow_redirects=True)
    assert response.status_code == 200
    assert b'User deactivated successfully' in response.data

def test_property_management_workflow(client, test_admin, test_user):
    # Login como admin
    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123'
    })

    # Criar nova propriedade
    response = client.post('/property/create', data={
        'nome': 'Test Property',
        'endereco': 'Test Address',
        'numero_apartamentos': 20
    })
    assert response.status_code == 302
    assert b'Property created successfully' in response.data

    # Verificar se a propriedade foi criada
    property = Property.query.filter_by(nome='Test Property').first()
    assert property is not None

    # Adicionar supervisor
    response = client.post(f'/property/{property.id}/add_supervisor', data={
        'supervisor_id': test_user.id
    })
    assert response.status_code == 302

    # Verificar se o supervisor foi adicionado
    property = Property.query.get(property.id)
    assert test_user in property.supervisors

    # Editar propriedade
    response = client.post('/property/1/edit', data={
        'nome': 'Edited Property',
        'endereco': 'Edited Address',
        'numero_apartamentos': 40
    })
    assert response.status_code == 302
    assert b'Property updated successfully' in response.data

    # Verificar se a propriedade foi atualizada
    property = Property.query.get(property.id)
    assert property.nome == 'Edited Property'
    assert property.endereco == 'Edited Address'
    assert property.numero_apartamentos == 40

    # Desativar propriedade
    response = client.post('/property/1/deactivate', follow_redirects=True)
    assert response.status_code == 200
    assert b'Property deactivated successfully' in response.data 