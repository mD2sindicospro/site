from app.extensions import db
from datetime import datetime

class Atividade(db.Model):
    __tablename__ = 'atividades'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100))
    descricao = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default='pendente')  # pendente, em_andamento, concluida
    resolvida = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_lancamento = db.Column(db.DateTime, default=datetime.utcnow)
    data_entrega = db.Column(db.DateTime)
    data_conclusao = db.Column(db.DateTime)
    condominio_id = db.Column(db.Integer, db.ForeignKey('condominios.id'), nullable=False)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    criado_por_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    condominio = db.relationship('Condominio', back_populates='atividades')
    responsavel = db.relationship('User', foreign_keys=[responsavel_id], back_populates='atividades_responsavel')
    criado_por = db.relationship('User', foreign_keys=[criado_por_id], back_populates='atividades_criadas')

    VALID_STATUS = ['pendente', 'em_andamento', 'concluida']

    def __init__(self, titulo=None, descricao=None, condominio_id=None, responsavel_id=None, data_entrega=None, status='pendente', resolvida=False, is_active=True, criado_por_id=None, data_criacao=None, data_conclusao=None, data_lancamento=None, **kwargs):
        if not condominio_id:
            raise ValueError('Condomínio é obrigatório')
        if not responsavel_id:
            raise ValueError('Responsável é obrigatório')
        if status not in self.VALID_STATUS:
            raise ValueError(f'Status inválido. Valores permitidos: {", ".join(self.VALID_STATUS)}')

        if data_entrega:
            if isinstance(data_entrega, str):
                data_entrega = datetime.strptime(data_entrega, '%Y-%m-%d')
            if data_entrega.date() < datetime.utcnow().date():
                raise ValueError('Data de entrega não pode ser no passado')
            
        self.titulo = titulo
        self.descricao = descricao
        self.condominio_id = condominio_id
        self.responsavel_id = responsavel_id
        self.data_entrega = data_entrega
        self.status = status
        self.resolvida = resolvida
        self.is_active = is_active
        self.criado_por_id = criado_por_id
        self.data_criacao = data_criacao or datetime.utcnow()
        self.data_lancamento = data_lancamento or datetime.utcnow()
        self.data_conclusao = data_conclusao
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def created_at(self):
        return self.data_criacao

    def concluir(self):
        self.status = 'concluida'
        self.resolvida = True
        self.data_conclusao = datetime.utcnow()

    def set_status(self, status):
        if status not in self.VALID_STATUS:
            raise ValueError(f"Status inválido: {status}. Valores permitidos: {self.VALID_STATUS}")
        self.status = status
        if status == 'concluida':
            self.concluir()

    def __repr__(self):
        return f'<Atividade {self.titulo}>' 