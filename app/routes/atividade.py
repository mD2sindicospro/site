from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.atividade import Atividade
from app.models.condominio import Condominio
from app.models.user import User
from app.extensions import db
from datetime import datetime
from app.forms.atividade import NovaAtividadeForm

atividade = Blueprint('atividade', __name__, url_prefix='/atividade')

@atividade.route('/')
@login_required
def list():
    """Lista todas as atividades do usuário."""
    if current_user.is_admin:
        atividades = Atividade.query.all()
    elif current_user.is_supervisor:
        atividades = Atividade.query.filter(
            (Atividade.responsavel_id == current_user.id) |
            (Atividade.criado_por_id == current_user.id)
        ).all()
    else:
        atividades = Atividade.query.filter_by(responsavel_id=current_user.id).all()
    
    condominios = Condominio.query.filter_by(is_active=True).all()
    usuarios = User.query.filter_by(is_active=True).all()
    return render_template('atividade/list.html', atividades=atividades, condominios=condominios, users=usuarios)

@atividade.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role not in ['admin', 'supervisor']:
        flash('Você não tem permissão para criar atividades', 'danger')
        return redirect(url_for('main.home'))

    form = NovaAtividadeForm()
    form.condominio.choices = [(c.id, c.nome) for c in Condominio.query.filter_by(is_active=True).all()]
    form.responsavel.choices = [(u.id, u.username) for u in User.query.filter_by(is_active=True).all()]

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                atividade = Atividade(
                    titulo=form.titulo.data,
                    descricao=form.descricao.data,
                    condominio_id=form.condominio.data,
                    responsavel_id=form.responsavel.data,
                    data_entrega=form.data_entrega.data,
                    status='pendente'
                )
                db.session.add(atividade)
                db.session.commit()
                flash('Atividade criada com sucesso', 'success')
                return redirect(url_for('atividade.list'))
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao criar atividade: {str(e)}', 'danger')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Erro no campo {field}: {error}', 'danger')

    return render_template('atividade/create.html', form=form)

@atividade.route('/<int:id>/update', methods=['POST'])
@login_required
def update(id):
    atividade = Atividade.query.get_or_404(id)
    
    if not current_user.is_admin and current_user.id != atividade.responsavel_id:
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))
        
    try:
        status = request.form.get('status')
        descricao = request.form.get('descricao')
        
        if status and status not in ['pendente', 'em_andamento', 'concluida']:
            raise ValueError('Status inválido')
            
        if status:
            atividade.status = status
        if descricao:
            atividade.descricao = descricao
            
        db.session.commit()
        flash('Atividade atualizada com sucesso', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar atividade: {str(e)}', 'danger')
        
    return redirect(url_for('atividade.list'))

@atividade.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    atividade = Atividade.query.get_or_404(id)
    
    if not current_user.is_admin and current_user.id != atividade.responsavel_id:
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))
        
    try:
        db.session.delete(atividade)
        db.session.commit()
        flash('Atividade excluída com sucesso', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir atividade: {str(e)}', 'danger')
        
    return redirect(url_for('atividade.list'))

@atividade.route('/<int:id>/concluir', methods=['POST'])
@login_required
def concluir(id):
    atividade = Atividade.query.get_or_404(id)
    
    if not current_user.is_admin and current_user.id != atividade.responsavel_id:
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))
        
    try:
        atividade.concluir()
        db.session.commit()
        flash('Atividade concluída com sucesso', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao concluir atividade: {str(e)}', 'danger')
        
    return redirect(url_for('atividade.list')) 