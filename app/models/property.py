from app.extensions import db
from datetime import datetime

class Property(db.Model):
    __tablename__ = 'property'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    number_of_apartments = db.Column(db.Integer, nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    entry_date = db.Column(db.DateTime)
    state = db.Column(db.String(2))
    administrator_name = db.Column(db.String(100))
    administrator_phone = db.Column(db.String(20))
    administrator_email = db.Column(db.String(100))
    logo_url = db.Column(db.String(500))

    # Relationships
    supervisor = db.relationship('User', back_populates='properties_supervisionados')
    activities = db.relationship('Activity', back_populates='property')

    def __init__(self, name=None, address=None, number_of_apartments=None, supervisor_id=None, 
                 is_active=True, entry_date=None, state=None, administrator_name=None, 
                 administrator_phone=None, administrator_email=None, logo_url=None, **kwargs):
        self.name = name
        self.address = address
        self.number_of_apartments = number_of_apartments
        self.supervisor_id = supervisor_id
        self.is_active = is_active
        self.entry_date = entry_date
        self.state = state
        self.administrator_name = administrator_name
        self.administrator_phone = administrator_phone
        self.administrator_email = administrator_email
        self.logo_url = logo_url
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f'<Property {self.name}>' 