from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, DateField
from wtforms.validators import DataRequired, Length

class NovaAtividadeForm(FlaskForm):
    atividade = StringField('Atividade', validators=[DataRequired(), Length(min=3, max=100)])
    descricao = TextAreaField('Descrição', validators=[DataRequired(), Length(min=10, max=500)])
    condominio = SelectField('Condomínio', coerce=int, validators=[DataRequired()])
    responsavel = SelectField('Responsável', coerce=int, validators=[DataRequired()])
    data_entrega = DateField('Data de Entrega', format='%Y-%m-%d', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada')
    ], validators=[DataRequired()])
    resolvida = BooleanField('Resolvida') 