from app.extensions import db
from datetime import datetime

class Mensagem(db.Model):
    __tablename__ = 'mensagens'
    
    id = db.Column(db.Integer, primary_key=True)
    destinatario_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    remetente_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    assunto = db.Column(db.String(120), nullable=False)
    corpo = db.Column(db.Text, nullable=False)
    lida = db.Column(db.Boolean, default=False, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    destinatario = db.relationship('User', foreign_keys=[destinatario_id], back_populates='mensagens_recebidas')
    remetente = db.relationship('User', foreign_keys=[remetente_id], back_populates='mensagens_enviadas')

    def __repr__(self):
        return f'<Mensagem {self.id} para {self.destinatario_id}>' 