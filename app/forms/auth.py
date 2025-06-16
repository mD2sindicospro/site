from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, ValidationError
from app.models.user import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='O email é obrigatório'),
        Email(message='Por favor, insira um email válido')
    ])
    remember = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('Email não encontrado')
        if not user.is_active:
            raise ValidationError('Usuário inativo. Entre em contato com o administrador.')

class RegistrationForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Tipo de Usuário', choices=[
        ('user', 'Normal'),
        ('supervisor', 'Supervisor'),
        ('admin', 'Administrador')
    ])
    submit = SubmitField('Registrar')

    def validate_name(self, name):
        user = User.query.filter_by(name=name.data).first()
        if user:
            raise ValidationError('Este nome já está em uso. Por favor, escolha outro.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este email já está em uso. Por favor, escolha outro.') 