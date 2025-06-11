from app.extensions import db
from datetime import datetime

# Importa todos os modelos
from app.models.user import User
from app.models.condominio import Condominio
from app.models.atividade import Atividade
from app.models.address import Address

# Garante que todas as tabelas sejam criadas
__all__ = [
    'User',
    'Condominio',
    'Atividade',
    'Address'
] 