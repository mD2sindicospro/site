from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.condominio import Condominio
from app.models.user import User
from app.extensions import db
from datetime import datetime

condominio = Blueprint('condominio', __name__, url_prefix='/condominio')

@condominio.route('/', methods=['GET', 'POST'])
@login_required
def list():
    if request.method == 'POST':
        nome = request.form.get('nome')
        endereco = request.form.get('endereco')
        numero_apartamentos = request.form.get('numero_apartamentos')
        supervisor_id = current_user.id if current_user.role == 'supervisor' else request.form.get('supervisor_id')
        data_entrada_str = request.form.get('data_entrada')
        is_active = request.form.get('is_active') == '1'
        administrador_nome = request.form.get('administrador_nome')
        administrador_telefone = request.form.get('administrador_telefone')
        administrador_email = request.form.get('administrador_email')
        estado = request.form.get('estado')
        data_entrada = None
        if data_entrada_str:
            try:
                if '/' in data_entrada_str:
                    data_entrada = datetime.strptime(data_entrada_str, '%d/%m/%Y').date()
                else:
                    data_entrada = datetime.strptime(data_entrada_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Data de entrada inválida. Use o formato correto.', 'danger')
                return redirect(url_for('condominio.list'))
        if not all([nome, endereco, numero_apartamentos]):
            flash('Todos os campos obrigatórios devem ser preenchidos.', 'danger')
            return redirect(url_for('condominio.list'))
        try:
            numero_apartamentos = int(numero_apartamentos)
            if numero_apartamentos <= 0:
                raise ValueError('Número de apartamentos deve ser maior que zero')
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('condominio.list'))
        try:
            condominio = Condominio(
                nome=nome,
                endereco=endereco,
                numero_apartamentos=numero_apartamentos,
                supervisor_id=supervisor_id,
                data_entrada=data_entrada,
                is_active=is_active,
                administrador_nome=administrador_nome,
                administrador_telefone=administrador_telefone,
                administrador_email=administrador_email,
                estado=estado
            )
            db.session.add(condominio)
            db.session.commit()
            flash('Condomínio criado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar condomínio: {str(e)}', 'danger')
        return redirect(url_for('condominio.list'))
    # GET: Listar condomínios
    if current_user.is_admin:
        condominios = Condominio.query.all()
    elif current_user.is_supervisor:
        condominios = Condominio.query.filter_by(supervisor_id=current_user.id).all()
    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('main.home'))
    supervisores = User.query.filter_by(role='supervisor', is_active=True).all()
    return render_template('condominio/list.html', condominios=condominios, supervisores=supervisores)

@condominio.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    condominio = Condominio.query.get_or_404(id)
    
    if not current_user.is_admin and current_user.id != condominio.supervisor_id:
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))
        
    if request.method == 'POST':
        nome = request.form.get('nome')
        endereco = request.form.get('endereco')
        numero_apartamentos = request.form.get('numero_apartamentos')
        supervisor_id = request.form.get('supervisor_id')
        data_entrada_str = request.form.get('data_entrada')
        estado = request.form.get('estado')
        administrador_nome = request.form.get('administrador_nome')
        administrador_telefone = request.form.get('administrador_telefone')
        administrador_email = request.form.get('administrador_email')
        is_active = request.form.get('is_active') == '1'
        data_entrada = None
        if data_entrada_str:
            try:
                if '/' in data_entrada_str:
                    data_entrada = datetime.strptime(data_entrada_str, '%d/%m/%Y').date()
                else:
                    data_entrada = datetime.strptime(data_entrada_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Data de entrada inválida. Use o formato correto.', 'danger')
                return redirect(url_for('condominio.list'))
        
        if not all([nome, endereco, numero_apartamentos]):
            flash('Todos os campos são obrigatórios', 'danger')
            supervisores = User.query.filter_by(role='supervisor').all()
            return render_template('condominio/list.html', condominio=condominio, supervisores=supervisores)
        
        try:
            numero_apartamentos = int(numero_apartamentos)
            if numero_apartamentos <= 0:
                raise ValueError
        except ValueError:
            flash('Número de apartamentos deve ser um número positivo.', 'danger')
            supervisores = User.query.filter_by(role='supervisor').all()
            return render_template('condominio/list.html', condominio=condominio, supervisores=supervisores)
        
        condominio.nome = nome
        condominio.endereco = endereco
        condominio.numero_apartamentos = numero_apartamentos
        condominio.data_entrada = data_entrada
        condominio.estado = estado
        condominio.administrador_nome = administrador_nome
        condominio.administrador_telefone = administrador_telefone
        condominio.administrador_email = administrador_email
        condominio.is_active = is_active
        if current_user.is_admin:
            condominio.supervisor_id = int(supervisor_id) if supervisor_id else None
        
        db.session.commit()
        
        flash('Condomínio atualizado com sucesso', 'success')
        return redirect(url_for('condominio.list'))
    
    supervisores = User.query.filter_by(role='supervisor').all()
    return render_template('condominio/list.html', condominio=condominio, supervisores=supervisores)

@condominio.route('/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_condominio(id):
    if not current_user.is_admin():
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))
        
    condominio = Condominio.query.get_or_404(id)
    condominio.is_active = not condominio.is_active
    db.session.commit()
    
    status = 'ativado' if condominio.is_active else 'desativado'
    flash(f'Condomínio {status} com sucesso', 'success')
    return redirect(url_for('condominio.list'))

@condominio.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if not current_user.is_admin():
        flash('Você não tem permissão para excluir condomínios.', 'danger')
        return redirect(url_for('condominio.list'))
    
    condominio = Condominio.query.get_or_404(id)
    db.session.delete(condominio)
    db.session.commit()
    flash('Condomínio excluído com sucesso!', 'success')
    return redirect(url_for('condominio.list')) 