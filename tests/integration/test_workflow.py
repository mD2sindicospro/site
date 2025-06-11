import pytest
from app.models.user import User
from app.models.condominio import Condominio
from app.models.atividade import Atividade
from app.extensions import db

def test_complete_workflow(client, test_user, test_admin):
    """Testa um fluxo completo de criação e gerenciamento de atividades."""
    # 1. Login como admin
    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'admin123'
    })
    
    # 2. Criar um novo condomínio
    response = client.post('/condominio/create', data={
        'nome': 'Condominio Teste',
        'endereco': 'Rua Teste, 123',
        'numero_apartamentos': 50
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Condominio criado com sucesso' in response.data
    
    # 3. Buscar o ID do condomínio criado
    condominio = Condominio.query.filter_by(nome='Condominio Teste').first()
    assert condominio is not None
    
    # 4. Criar uma nova atividade
    response = client.post('/atividade/create', data={
        'titulo': 'Atividade Teste',
        'descricao': 'Descrição da atividade teste',
        'condominio': 1,
        'responsavel': test_user.id,
        'data_entrega': '2024-12-31',
        'status': 'pendente'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Atividade criada com sucesso' in response.data
    
    # 5. Logout como admin
    client.get('/auth/logout')
    
    # 6. Login como usuário normal
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    # 7. Verificar se a atividade está visível
    response = client.get('/atividade/')
    assert response.status_code == 200
    assert b'Manutencao do Elevador' in response.data
    
    # 8. Atualizar o status da atividade
    atividade = Atividade.query.filter_by(titulo='Manutencao do Elevador').first()
    response = client.post(f'/atividade/{atividade.id}/update', data={
        'status': 'em_andamento',
        'descricao': 'Descrição atualizada'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Atividade atualizada com sucesso' in response.data
    
    # 9. Finalizar a atividade
    response = client.post(f'/atividade/{atividade.id}/update', data={
        'status': 'concluida',
        'descricao': 'Elevador verificado e funcionando normalmente'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Atividade atualizada com sucesso' in response.data

def test_user_management_workflow(client, test_admin):
    """Testa o fluxo de gerenciamento de usuários."""
    # 1. Login como admin
    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'admin123'
    })
    
    # 2. Criar novo usuário
    response = client.post('/admin/user/create', data={
        'username': 'novousuario',
        'email': 'novo@example.com',
        'password': 'senha123',
        'role': 'user'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Usuario criado com sucesso' in response.data
    
    # 3. Verificar se o usuário foi criado
    user = User.query.filter_by(email='novo@example.com').first()
    assert user is not None
    assert user.username == 'novousuario'
    
    # 4. Editar usuário
    response = client.post('/admin/user/2/edit', data={
        'username': 'usuarioeditado',
        'email': 'editado@example.com',
        'role': 'user',
        'is_active': True
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Usuario atualizado com sucesso' in response.data
    
    # 5. Verificar alterações
    user = User.query.filter_by(email='novo@example.com').first()
    assert user.username == 'usuarioeditado'
    assert user.role == 'user'
    
    # 6. Desativar usuário
    response = client.post('/admin/user/2/deactivate', follow_redirects=True)
    assert response.status_code == 200
    assert b'Usuario desativado com sucesso' in response.data
    
    # 7. Verificar desativação
    user = User.query.filter_by(email='novo@example.com').first()
    assert user.is_active is False

def test_condominio_management_workflow(client, test_admin, test_user):
    """Testa o fluxo de gerenciamento de condomínios."""
    # 1. Login como admin
    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'admin123'
    })
    
    # 2. Criar novo condomínio
    response = client.post('/condominio/create', data={
        'nome': 'Novo Condominio',
        'endereco': 'Nova Rua, 456',
        'numero_apartamentos': 30
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Condominio criado com sucesso' in response.data
    
    # 3. Buscar o condomínio criado
    condominio = Condominio.query.filter_by(nome='Novo Condominio').first()
    assert condominio is not None
    
    # 4. Adicionar supervisor
    response = client.post(f'/condominio/{condominio.id}/add_supervisor', data={
        'user_id': test_user.id
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Supervisor adicionado com sucesso' in response.data
    
    # 5. Verificar supervisor
    condominio = Condominio.query.get(condominio.id)
    assert test_user in condominio.supervisores
    
    # 6. Editar condomínio
    response = client.post('/condominio/1/edit', data={
        'nome': 'Condominio Editado',
        'endereco': 'Rua Editada, 789',
        'numero_apartamentos': 40,
        'supervisor_id': test_user.id
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Condominio atualizado com sucesso' in response.data
    
    # 7. Verificar alterações
    condominio = Condominio.query.get(condominio.id)
    assert condominio.nome == 'Condominio Editado'
    assert condominio.endereco == 'Rua Editada, 789'
    assert condominio.numero_apartamentos == 40
    
    # 8. Desativar condomínio
    response = client.post('/condominio/1/deactivate', follow_redirects=True)
    assert response.status_code == 200
    assert b'Condominio desativado com sucesso' in response.data 