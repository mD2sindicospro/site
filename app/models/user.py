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
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user', nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    deactivated_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    # addresses = db.relationship('Address', back_populates='user', cascade='all, delete-orphan', lazy='joined')
    properties_supervisionados = db.relationship('Property', back_populates='supervisor')
    activities_responsible = db.relationship('Activity', foreign_keys='Activity.responsible_id', back_populates='responsible')
    activities_created = db.relationship('Activity', foreign_keys='Activity.created_by_id', back_populates='created_by')
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', back_populates='sender')
    messages_received = db.relationship('Message', foreign_keys='Message.receiver_id', back_populates='receiver')

    # Lista de papéis válidos
    VALID_ROLES = ['user', 'supervisor', 'admin']

    def __init__(self, email, password=None, role='user', is_active=True, name=None):
        if not email:
            raise ValueError("Email é obrigatório")
        if not name:
            raise ValueError("Nome é obrigatório")
        if role not in self.VALID_ROLES:
            raise ValueError(f"Papel inválido. Papéis válidos são: {', '.join(self.VALID_ROLES)}")
        self.email = email
        self.role = role
        self.is_active = is_active
        self.name = name
        if password:
            self.set_password(password)

    def set_password(self, password):
        if not password:
            raise ValueError('Senha é obrigatória')
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash or not isinstance(self.password_hash, str) or len(self.password_hash) < 10:
            return False
        try:
            return check_password_hash(self.password_hash, password)
        except Exception:
            return False

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

    def __repr__(self):
        return f'<User {self.name}>' 