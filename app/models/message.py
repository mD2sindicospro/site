from app.extensions import db
from datetime import datetime

class Message(db.Model):
    __tablename__ = 'message'
    
    id = db.Column(db.Integer, primary_key=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    subject = db.Column(db.String(120), nullable=False)
    body = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    receiver = db.relationship('User', foreign_keys=[receiver_id], back_populates='messages_received')
    sender = db.relationship('User', foreign_keys=[sender_id], back_populates='messages_sent')

    def __repr__(self):
        return f'<Message {self.id} to {self.receiver_id}>' 