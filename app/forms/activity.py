from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, DateField
from wtforms.validators import DataRequired, Length
from app.models.activity import Activity

class NewActivityForm(FlaskForm):
    title = StringField('Atividade', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Descrição', validators=[DataRequired(), Length(min=10, max=500)])
    property = SelectField('Condomínio', coerce=int, validators=[DataRequired()])
    responsible = SelectField('Responsável', coerce=int, validators=[DataRequired()])
    delivery_date = DateField('Data de Entrega', format='%Y-%m-%d', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('pending', 'Pendente'),
        ('in_progress', 'Em Andamento'),
        ('completed', 'Concluída'),
        ('cancelled', 'Cancelada')
    ], validators=[DataRequired()])
    resolved = BooleanField('Resolvida') 