from app.extensions import db, bcrypt, login_manager
from flask_login import UserMixin
from datetime import datetime
import re
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user', nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    deactivated_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    addresses = db.relationship('Address', back_populates='user', cascade='all, delete-orphan', lazy='joined')
    condominios_supervisionados = db.relationship('Condominio', back_populates='supervisor', lazy=True)
    atividades_responsavel = db.relationship('Atividade', foreign_keys='Atividade.responsavel_id', back_populates='responsavel', lazy=True)
    atividades_criadas = db.relationship('Atividade', foreign_keys='Atividade.criado_por_id', back_populates='criado_por', lazy=True)
    mensagens_enviadas = db.relationship('Mensagem', foreign_keys='Mensagem.remetente_id', back_populates='remetente', lazy=True)
    mensagens_recebidas = db.relationship('Mensagem', foreign_keys='Mensagem.destinatario_id', back_populates='destinatario', lazy=True)

    # Lista de papéis válidos
    VALID_ROLES = ['user', 'supervisor', 'admin']

    def __init__(self, username, email, password=None, role='user', is_active=True, name=None):
        if not username or not email:
            raise ValueError("Username e email são obrigatórios")
        
        if role not in self.VALID_ROLES:
            raise ValueError(f"Papel inválido. Papéis válidos são: {', '.join(self.VALID_ROLES)}")
        
        self.username = username
        self.email = email
        self.role = role
        self.is_active = is_active
        self.name = name
        
        if password:
            self.set_password(password)

    def set_password(self, password):
        if not password:
            raise ValueError('Senha é obrigatória')
        if len(password) < 6:
            raise ValueError('Senha deve ter no mínimo 6 caracteres')
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def verify_password(self, password):
        return self.check_password(password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_supervisor(self):
        return self.role == 'supervisor'

    @property
    def is_user(self):
        return self.role == 'user'

    def deactivate(self):
        """Desativa o usuário."""
        self.is_active = False
        self.deactivated_at = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def activate(self):
        """Reativa o usuário."""
        self.is_active = True
        self.deactivated_at = None
        db.session.add(self)
        db.session.commit()

    @property
    def role(self):
        return self.__dict__.get('role', 'user')

    @role.setter
    def role(self, value):
        self.__dict__['role'] = value

    def __repr__(self):
        return f'<User {self.username}>' 