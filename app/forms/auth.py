from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, SelectField, PasswordField
from wtforms.validators import DataRequired, Length, Email, ValidationError
from app.models.user import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='O email é obrigatório'),
        Email(message='Por favor, insira um email válido')
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(message='A senha é obrigatória')
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
    password = PasswordField('Senha', validators=[
        DataRequired(message='A senha é obrigatória'),
        Length(min=6, message='A senha deve ter pelo menos 6 caracteres')
    ])
    confirm_password = PasswordField('Confirmar Senha', validators=[
        DataRequired(message='Confirme sua senha'),
        Length(min=6, message='A senha deve ter pelo menos 6 caracteres')
    ])
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
    
    def validate_confirm_password(self, confirm_password):
        if self.password.data != confirm_password.data:
            raise ValidationError('As senhas não coincidem') 