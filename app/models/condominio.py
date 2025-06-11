from app.extensions import db
from datetime import datetime

class Condominio(db.Model):
    __tablename__ = 'condominios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    endereco = db.Column(db.String(200), nullable=False)
    numero_apartamentos = db.Column(db.Integer, nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    supervisor = db.relationship('User', foreign_keys=[supervisor_id], back_populates='condominios_supervisionados')
    atividades = db.relationship('Atividade', back_populates='condominio', lazy=True)

    def __init__(self, nome=None, endereco=None, numero_apartamentos=None, supervisor_id=None, is_active=True, created_at=None, updated_at=None, **kwargs):
        if not nome:
            raise ValueError('Nome é obrigatório')
        if not endereco:
            raise ValueError('Endereço é obrigatório')
        if numero_apartamentos is None:
            raise ValueError('Número de apartamentos é obrigatório')
        if not isinstance(numero_apartamentos, int):
            raise ValueError('Número de apartamentos deve ser um número inteiro')
        if numero_apartamentos <= 0:
            raise ValueError('Número de apartamentos deve ser maior que zero')
        if not supervisor_id:
            raise ValueError('Supervisor é obrigatório')
            
        self.nome = nome
        self.endereco = endereco
        self.numero_apartamentos = numero_apartamentos
        self.supervisor_id = supervisor_id
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f'<Condominio {self.nome}>' 