from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from app.extensions import db, bcrypt
from app.models.user import User
from app.forms.auth import LoginForm

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST' and form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Usuário inativo. Entre em contato com o administrador.', 'danger')
                return render_template('auth/login.html', form=form)
            login_user(user)
            flash('Bem-vindo!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Email ou senha inválidos', 'danger')
            
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado', 'info')
    return redirect(url_for('auth.login')) 