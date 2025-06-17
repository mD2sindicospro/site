from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.activity import Activity
from app.models.property import Property
from app.models.user import User
from app.extensions import db
from datetime import datetime
from app.forms.activity import NewActivityForm
from flask_wtf.csrf import generate_csrf

activity = Blueprint('activity', __name__, url_prefix='/activity')

@activity.route('/')
@login_required
def list():
    """List all activities for the user."""
    if current_user.is_admin:
        activities = Activity.query.all()
    elif current_user.is_supervisor:
        activities = Activity.query.filter(
            (Activity.responsible_id == current_user.id) |
            (Activity.created_by_id == current_user.id)
        ).all()
    else:
        activities = Activity.query.filter_by(responsible_id=current_user.id).all()
    
    properties = Property.query.filter_by(is_active=True).all()
    users = User.query.filter_by(is_active=True).all()
    return render_template('activity/list.html', activities=activities, properties=properties, users=users)

@activity.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role not in ['admin', 'supervisor']:
        flash('Você não tem permissão para criar atividades', 'danger')
        return redirect(url_for('main.home'))

    form = NewActivityForm()
    form.property.choices = [(p.id, p.name) for p in Property.query.filter_by(is_active=True).all()]
    form.responsible.choices = [(u.id, u.name) for u in User.query.filter_by(is_active=True).all()]
    
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                activity = Activity(
                    title=form.title.data,
                    description=form.description.data,
                    property_id=form.property.data,
                    responsible_id=form.responsible.data,
                    delivery_date=form.delivery_date.data,
                    status='pending',
                    created_by_id=current_user.id
                )
                db.session.add(activity)
                db.session.commit()
                flash('Atividade criada com sucesso', 'success')
                return redirect(url_for('activity.list'))
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao criar atividade: {str(e)}', 'danger')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Erro no campo {field}: {error}', 'danger')
    # Em qualquer outro caso, redireciona para a lista de atividades
    return redirect(url_for('activity.list'))

@activity.route('/<int:id>/update', methods=['POST'])
@login_required
def update(id):
    activity = Activity.query.get_or_404(id)
    
    if not current_user.is_admin and current_user.id != activity.responsible_id:
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))
        
    try:
        status = request.form.get('status')
        description = request.form.get('description')
        
        if status and status not in ['pending', 'in_progress', 'completed']:
            raise ValueError('Status inválido')
            
        if status:
            activity.status = status
        if description:
            activity.description = description
            
        db.session.commit()
        flash('Atividade atualizada com sucesso', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar atividade: {str(e)}', 'danger')
        
    return redirect(url_for('activity.list'))
    
@activity.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    activity = Activity.query.get_or_404(id)
    
    if not current_user.is_admin and current_user.id != activity.responsible_id:
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))
        
    try:
        db.session.delete(activity)
        db.session.commit()
        flash('Atividade excluída com sucesso', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir atividade: {str(e)}', 'danger')
        
    return redirect(url_for('activity.list'))

@activity.route('/<int:id>/complete', methods=['POST'])
@login_required
def complete(id):
    activity = Activity.query.get_or_404(id)
    
    if not current_user.is_admin and current_user.id != activity.responsible_id:
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))
        
    try:
        activity.status = 'completed'
        db.session.commit()
        flash('Atividade concluída com sucesso', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao concluir atividade: {str(e)}', 'danger')
        
    return redirect(url_for('activity.list'))

@activity.route('/api/choices')
@login_required
def api_choices():
    properties = Property.query.filter_by(is_active=True).all()
    responsaveis = User.query.filter_by(is_active=True).all()
    return jsonify({
        'properties': [{'id': p.id, 'nome': p.name} for p in properties],
        'responsaveis': [{'id': u.id, 'nome': u.name} for u in responsaveis],
        'csrf_token': generate_csrf()
    }) 