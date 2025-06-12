from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.condominio import Condominio
from app.models.user import User
from app.extensions import db
from datetime import datetime

condominio = Blueprint('condominio', __name__, url_prefix='/condominio')

@condominio.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role not in ['admin', 'supervisor']:
        flash('Você não tem permissão para criar condomínios', 'danger')
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        endereco = request.form.get('endereco')
        numero_apartamentos = request.form.get('numero_apartamentos')
        supervisor_id = current_user.id if current_user.role == 'supervisor' else request.form.get('supervisor_id')
        
        if not all([nome, endereco, numero_apartamentos]):
            flash('Todos os campos são obrigatórios', 'danger')
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
                supervisor_id=supervisor_id
            )
            db.session.add(condominio)
            db.session.commit()
            flash('Condomínio criado com sucesso', 'success')
            return redirect(url_for('condominio.list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar condomínio: {str(e)}', 'danger')
            return redirect(url_for('condominio.list'))
    
    supervisores = User.query.filter_by(role='supervisor', is_active=True).all()
    return render_template('condominio/create.html', supervisores=supervisores)

@condominio.route('/')
@login_required
def list():
    if current_user.is_admin():
        condominios = Condominio.query.all()
    elif current_user.is_supervisor():
        condominios = Condominio.query.filter_by(supervisor_id=current_user.id).all()
    else:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('main.home'))
    
    return render_template('condominio/list.html', condominios=condominios)

@condominio.route('/condominios', methods=['GET', 'POST'])
@login_required
def listar_condominios():
    if request.method == 'POST' and request.form.get('excluir_condominio_id'):
        if not current_user.is_admin():
            flash('Você não tem permissão para excluir condomínios.', 'danger')
            return redirect(url_for('condominio.listar_condominios'))
        condominio_id = request.form.get('excluir_condominio_id')
        condominio = Condominio.query.get(condominio_id)
        if condominio:
            db.session.delete(condominio)
            db.session.commit()
            flash('Condomínio excluído com sucesso!', 'success')
        else:
            flash('Condomínio não encontrado.', 'danger')
        return redirect(url_for('condominio.listar_condominios'))
    if request.method == 'POST' and request.form.get('edit_condominio_id'):
        condominio_id = request.form.get('edit_condominio_id')
        condominio = Condominio.query.get(condominio_id)
        if not condominio:
            flash('Condomínio não encontrado.', 'danger')
            return redirect(url_for('condominio.listar_condominios'))
        if not (current_user.is_admin() or current_user.id == condominio.supervisor_id or current_user.is_supervisor()):
            flash('Você não tem permissão para editar este condomínio.', 'danger')
            return redirect(url_for('condominio.listar_condominios'))
        condominio.nome = request.form.get('edit_nome')
        condominio.endereco = request.form.get('edit_endereco')
        condominio.numero_apartamentos = request.form.get('edit_numero_apartamentos')
        condominio.administrador = request.form.get('edit_administrador')
        condominio.contato = request.form.get('edit_contato')
        condominio.email = request.form.get('edit_email')
        data_entrada_str = request.form.get('edit_data_entrada')
        if data_entrada_str:
            try:
                condominio.data_entrada = datetime.strptime(data_entrada_str, '%d/%m/%Y').date()
            except ValueError:
                flash('Data de entrada inválida. Use o formato dd/mm/aaaa.', 'danger')
                return redirect(url_for('condominio.listar_condominios'))
        else:
            condominio.data_entrada = None
        if current_user.is_admin():
            supervisor_id = request.form.get('edit_supervisor_id')
            condominio.supervisor_id = int(supervisor_id) if supervisor_id else None
        db.session.commit()
        flash('Condomínio atualizado com sucesso!', 'success')
        return redirect(url_for('condominio.listar_condominios'))
    if request.method == 'POST' and request.form.get('ativar_inativar_condominio_id'):
        condominio_id = request.form.get('ativar_inativar_condominio_id')
        novo_status = request.form.get('novo_status_condominio') == '1'
        condominio = Condominio.query.get(condominio_id)
        if not condominio:
            flash('Condomínio não encontrado.', 'danger')
            return redirect(url_for('condominio.listar_condominios'))
        if not (current_user.is_admin() or current_user.is_supervisor()):
            flash('Você não tem permissão para alterar o status deste condomínio.', 'danger')
            return redirect(url_for('condominio.listar_condominios'))
        condominio.is_active = novo_status
        db.session.commit()
        flash(f'Condomínio {"ativado" if novo_status else "inativado"} com sucesso!', 'success')
        return redirect(url_for('condominio.listar_condominios'))
    supervisores = User.query.filter(User.is_active == True, User.role.in_(['admin', 'supervisor'])).all()
    return render_template('condominio/listar.html', condominios=condominios, supervisores=supervisores)

@condominio.route('/condominio/novo', methods=['GET', 'POST'])
@login_required
def novo_condominio():
    if not (current_user.is_admin() or current_user.is_supervisor()):
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        endereco = request.form.get('endereco')
        numero_apartamentos = request.form.get('numero_apartamentos')
        data_entrada_str = request.form.get('data_entrada')
        administrador = request.form.get('administrador')
        contato = request.form.get('contato')
        email = request.form.get('email')
        
        data_entrada = None
        if data_entrada_str:
            try:
                data_entrada = datetime.strptime(data_entrada_str, '%d/%m/%Y').date()
            except ValueError:
                flash('Data de entrada inválida. Use o formato dd/mm/aaaa.', 'danger')
                return redirect(url_for('condominio.listar_condominios'))
        
        supervisor_id = request.form.get('novo_supervisor_id')
        condominio = Condominio(
            nome=nome,
            endereco=endereco,
            numero_apartamentos=numero_apartamentos,
            supervisor_id=int(supervisor_id) if supervisor_id else None,
            data_entrada=data_entrada,
            administrador=administrador,
            contato=contato,
            email=email
        )
        
        db.session.add(condominio)
        db.session.commit()
        
        flash('Condomínio cadastrado com sucesso!', 'success')
        return redirect(url_for('condominio.listar_condominios'))
    
    supervisores = User.query.filter(User.is_active == True, User.role.in_(['admin', 'supervisor'])).all()
    return render_template('condominio/novo.html', supervisores=supervisores)

@condominio.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    condominio = Condominio.query.get_or_404(id)
    
    if not current_user.is_admin() and current_user.id != condominio.supervisor_id:
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))
        
    if request.method == 'POST':
        nome = request.form.get('nome')
        endereco = request.form.get('endereco')
        numero_apartamentos = request.form.get('numero_apartamentos')
        supervisor_id = request.form.get('supervisor_id')
        
        if not all([nome, endereco, numero_apartamentos]):
            flash('Todos os campos são obrigatórios', 'danger')
            return render_template('condominio/edit.html', condominio=condominio)
            
        try:
            numero_apartamentos = int(numero_apartamentos)
            if numero_apartamentos <= 0:
                raise ValueError
        except ValueError:
            flash('Número de apartamentos deve ser um número positivo.', 'danger')
            return render_template('condominio/edit.html', condominio=condominio)
            
        condominio.nome = nome
        condominio.endereco = endereco
        condominio.numero_apartamentos = numero_apartamentos
        if current_user.is_admin():
            condominio.supervisor_id = int(supervisor_id) if supervisor_id else None
        
        db.session.commit()
        
        flash('Condomínio atualizado com sucesso', 'success')
        return redirect(url_for('condominio.list'))
        
    return render_template('condominio/edit.html', condominio=condominio)

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
    return redirect(url_for('condominio.listar_condominios')) 