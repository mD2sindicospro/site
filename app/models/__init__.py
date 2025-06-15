from app.extensions import db
from datetime import datetime

# Importa todos os modelos
from app.models.user import User
from app.models.property import Property
from app.models.activity import Activity
from app.models.message import Message
# from app.models.address import Address

# Garante que todas as tabelas sejam criadas
__all__ = [
    'User',
    'Property',
    'Activity',
    'Message'
] 