from app.extensions import db
from datetime import datetime

class Activity(db.Model):
    __tablename__ = 'activity'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    responsible_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    delivery_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    cancellation_reason = db.Column(db.Text)
    correction_reason = db.Column(db.Text)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    property = db.relationship('Property', back_populates='activities')
    responsible = db.relationship('User', foreign_keys=[responsible_id], back_populates='activities_responsible')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id], backref=db.backref('approved_activities', lazy=True))
    created_by = db.relationship('User', foreign_keys=[created_by_id], back_populates='activities_created')

    def __repr__(self):
        return f'<Activity {self.title}>' 