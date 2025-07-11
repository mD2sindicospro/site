from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.user import User
from app.extensions import db
import flask

admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.route('/')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Acesso negado', 'danger')
        return redirect(url_for('main.home'))
    return render_template('admin/dashboard.html')

@admin.route('/users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if not current_user.is_admin:
        flash('Acesso negado', 'danger')
        return redirect(url_for('main.home'))

    # Cadastro de novo usuário (apenas admin)
    if request.method == 'POST' and not request.form.get('edit_user_id') and not request.form.get('inativar_user_id') and not request.form.get('excluir_user_id') and not request.form.get('ativar_user_id'):
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        is_active = request.form.get('is_active') == '1'
        if not password:
            flash('A senha é obrigatória.', 'danger')
            return redirect(url_for('admin.manage_users'))
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado', 'danger')
            return redirect(url_for('admin.manage_users'))
        
        # Criar usuário usando o método correto do modelo
        user = User(name=name, email=email, role=role)
        user.set_password(password)  # Usa o método scrypt do modelo
        user.is_active = is_active
        db.session.add(user)
        db.session.commit()
        flash('Usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('admin.manage_users'))

    # Edição de usuário (admin e supervisor)
    if request.method == 'POST' and request.form.get('edit_user_id'):
        if not (current_user.is_admin or current_user.is_supervisor):
            flash('Você não tem permissão para editar usuários.', 'danger')
            return redirect(url_for('admin.manage_users'))
        user_id = request.form.get('edit_user_id')
        user = User.query.get(user_id)
        if user:
            user.name = request.form.get('name')
            user.email = request.form.get('email')
            user.role = request.form.get('role')
            user.is_active = request.form.get('edit_is_active') == '1'
            new_password = request.form.get('edit_password')
            if new_password:
                user.set_password(new_password)  # Usa o método scrypt do modelo
            db.session.commit()
            flash('Usuário atualizado com sucesso!', 'success')
        else:
            flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('admin.manage_users'))

    # Inativação de usuário (admin e supervisor)
    if request.method == 'POST' and request.form.get('inativar_user_id'):
        if not (current_user.is_admin or current_user.is_supervisor):
            flash('Você não tem permissão para inativar usuários.', 'danger')
            return redirect(url_for('admin.manage_users'))
        user_id = request.form.get('inativar_user_id')
        user = User.query.get(user_id)
        if user:
            user.is_active = False
            db.session.commit()
            flash('Usuário inativado com sucesso!', 'success')
        else:
            flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('admin.manage_users'))

    # Ativação de usuário (admin e supervisor)
    if request.method == 'POST' and request.form.get('ativar_user_id'):
        if not (current_user.is_admin or current_user.is_supervisor):
            flash('Você não tem permissão para ativar usuários.', 'danger')
            return redirect(url_for('admin.manage_users'))
        user_id = request.form.get('ativar_user_id')
        user = User.query.get(user_id)
        if user:
            user.is_active = True
            db.session.commit()
            flash('Usuário ativado com sucesso!', 'success')
        else:
            flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('admin.manage_users'))

    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin.route('/user/create', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin:
        flash('Acesso negado', 'danger')
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        is_active = request.form.get('is_active') == 'on'
        
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado', 'danger')
            return redirect(url_for('admin.create_user'))
        
        user = User(name=name, email=email, role=role)
        user.set_password(password)  # Usa o método scrypt do modelo
        user.is_active = is_active
        
        db.session.add(user)
        db.session.commit()
        
        flash('Usuário criado com sucesso', 'success')
        return redirect(url_for('admin.manage_users'))
    
    return render_template('admin/create_user.html') 