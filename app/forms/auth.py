from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
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

    def validate_password(self, password):
        user = User.query.filter_by(email=self.email.data).first()
        if user and not user.verify_password(password.data):
            raise ValidationError('Senha incorreta')

class RegistrationForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Tipo de Usuário', choices=[
        ('normal', 'Normal'),
        ('supervisor', 'Supervisor'),
        ('admin', 'Administrador')
    ])
    submit = SubmitField('Registrar')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nome de usuário já está em uso. Por favor, escolha outro.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este email já está em uso. Por favor, escolha outro.') 