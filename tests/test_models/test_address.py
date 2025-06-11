import pytest
from app.models.address import Address
from app.models.user import User
from app.extensions import db

def test_create_address(app):
    """Testa a criação de um endereço"""
    with app.app_context():
        # Criar usuário
        user = User(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()

        # Criar endereço
        address = Address(
            user_id=user.id,
            street='Rua Teste',
            number='123',
            complement='Apto 45',
            neighborhood='Centro',
            city='São Paulo',
            state='SP',
            zip_code='01234-567',
            is_default=True
        )
        db.session.add(address)
        db.session.commit()

        assert address.id is not None
        assert address.user_id == user.id
        assert address.street == 'Rua Teste'
        assert address.number == '123'
        assert address.complement == 'Apto 45'
        assert address.neighborhood == 'Centro'
        assert address.city == 'São Paulo'
        assert address.state == 'SP'
        assert address.zip_code == '01234-567'
        assert address.is_default is True

def test_address_validation(app):
    """Testa as validações do modelo"""
    with app.app_context():
        # Criar usuário
        user = User(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()

        # Teste de CEP inválido
        with pytest.raises(ValueError):
            Address(
                user_id=user.id,
                street='Rua Teste',
                number='123',
                neighborhood='Centro',
                city='São Paulo',
                state='SP',
                zip_code='12345'  # CEP inválido
            )

        # Teste de estado inválido
        with pytest.raises(ValueError):
            Address(
                user_id=user.id,
                street='Rua Teste',
                number='123',
                neighborhood='Centro',
                city='São Paulo',
                state='XX',  # Estado inválido
                zip_code='01234-567'
            )

def test_address_update(app):
    """Testa a atualização de endereço"""
    with app.app_context():
        # Criar usuário
        user = User(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()

        # Criar endereço
        address = Address(
            user_id=user.id,
            street='Rua Teste',
            number='123',
            neighborhood='Centro',
            city='São Paulo',
            state='SP',
            zip_code='01234-567'
        )
        db.session.add(address)
        db.session.commit()

        # Atualizar endereço
        address.street = 'Avenida Atualizada'
        address.number = '456'
        address.complement = 'Sala 789'
        db.session.commit()

        updated_address = Address.query.get(address.id)
        assert updated_address.street == 'Avenida Atualizada'
        assert updated_address.number == '456'
        assert updated_address.complement == 'Sala 789'

def test_address_default_handling(app):
    """Testa o gerenciamento de endereço padrão"""
    with app.app_context():
        # Criar usuário
        user = User(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()

        # Criar primeiro endereço como padrão
        address1 = Address(
            user_id=user.id,
            street='Rua 1',
            number='123',
            neighborhood='Centro',
            city='São Paulo',
            state='SP',
            zip_code='01234-567',
            is_default=True
        )
        db.session.add(address1)
        db.session.commit()

        # Criar segundo endereço como padrão
        address2 = Address(
            user_id=user.id,
            street='Rua 2',
            number='456',
            neighborhood='Vila Nova',
            city='São Paulo',
            state='SP',
            zip_code='04567-890',
            is_default=True
        )
        db.session.add(address2)
        db.session.commit()

        # Verificar se o primeiro endereço não é mais padrão
        updated_address1 = Address.query.get(address1.id)
        assert updated_address1.is_default is False

        # Verificar se o segundo endereço é o padrão
        updated_address2 = Address.query.get(address2.id)
        assert updated_address2.is_default is True

def test_address_user_relationship(app):
    """Testa o relacionamento entre usuário e endereços"""
    with app.app_context():
        # Criar usuário
        user = User(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()

        # Criar múltiplos endereços para o usuário
        addresses = [
            Address(
                user_id=user.id,
                street=f'Rua {i}',
                number=str(i * 100),
                neighborhood=f'Bairro {i}',
                city='São Paulo',
                state='SP',
                zip_code=f'01234-{i:03d}'
            ) for i in range(1, 4)
        ]
        db.session.add_all(addresses)
        db.session.commit()

        # Verificar endereços do usuário
        user_addresses = Address.query.filter_by(user_id=user.id).all()
        assert len(user_addresses) == 3
        assert user_addresses[0].street == 'Rua 1'
        assert user_addresses[1].street == 'Rua 2'
        assert user_addresses[2].street == 'Rua 3' 