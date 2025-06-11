from app.extensions import db
from datetime import datetime
import re
from sqlalchemy.orm import validates

class Address(db.Model):
    __tablename__ = 'addresses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    street = db.Column(db.String(200), nullable=False)
    number = db.Column(db.String(20), nullable=False)
    complement = db.Column(db.String(100))
    neighborhood = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    user = db.relationship('User', back_populates='addresses', lazy='joined')

    @validates('street', 'number', 'neighborhood', 'city', 'zip_code', 'state')
    def validate_fields(self, key, value):
        if not value:
            raise ValueError(f'O campo {key} é obrigatório')
        if key == 'zip_code':
            if not re.match(r'^\d{5}-?\d{3}$', value):
                raise ValueError('CEP inválido. Use o formato 00000-000')
        if key == 'state':
            estados_validos = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 
                              'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
            if value.upper() not in estados_validos:
                raise ValueError('Estado inválido')
            return value.upper()
        return value

    def __init__(self, user_id, street, number, neighborhood, city, state, zip_code, complement=None, is_default=False):
        self.user_id = user_id
        self.street = street
        self.number = number
        self.complement = complement
        self.neighborhood = neighborhood
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.is_default = is_default

        # Se este endereço for padrão, desmarcar outros endereços padrão do usuário
        if is_default:
            Address.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})

    def __repr__(self):
        return f'<Address {self.street}, {self.number}>' 