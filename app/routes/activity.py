from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from app.models.activity import Activity
from app.models.property import Property
from app.models.user import User
from app.extensions import db
from datetime import datetime
from app.forms.activity import NewActivityForm, ImportActivitiesForm
from flask_wtf.csrf import generate_csrf
import os
import tempfile
from app.utils.excel_importer import ActivityExcelImporter

activity = Blueprint('activity', __name__, url_prefix='/activity')

@activity.route('/')
@login_required
def list():
    """List all activities for the user."""
    if not (current_user.is_admin or current_user.is_supervisor):
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('main.home'))
    

    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    property_id = request.args.get('property', type=int)
    responsible_id = request.args.get('responsible', type=int)
    status = request.args.get('status')
    if current_user.is_admin:
        query = Activity.query
    elif current_user.is_supervisor:
        query = Activity.query.filter(
            (Activity.responsible_id == current_user.id) |
            (Activity.created_by_id == current_user.id)
        )
    if property_id:
        query = query.filter(Activity.property_id == property_id)
    if responsible_id:
        query = query.filter(Activity.responsible_id == responsible_id)
    if status:
        query = query.filter(Activity.status == status)
    # Filtro para não mostrar atividades canceladas, não realizadas ou realizadas
    query = query.filter(~Activity.status.in_(['cancelled', 'not_completed', 'done']))
    total_activities = query.count()
    total_pages = max(1, (total_activities + per_page - 1) // per_page)
    # Garantir que a página atual seja válida
    page = max(1, min(page, total_pages))
    
    activities = query.order_by(Activity.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    properties = Property.query.filter_by(is_active=True).all()
    users = User.query.filter_by(is_active=True).all()
    
    return render_template('activity/list.html', activities=activities, properties=properties, users=users, total_paginas=total_pages, pagina_atual=page, property_id=property_id, responsible_id=responsible_id, status_filter=status)

@activity.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role not in ['admin', 'supervisor']:
        flash('Você não tem permissão para criar atividades', 'danger')
        return redirect(url_for('main.home'))

    new_activity_form = NewActivityForm()
    new_activity_form.property.choices = [(p.id, p.name) for p in Property.query.filter_by(is_active=True).all()]
    new_activity_form.responsible.choices = [(u.id, u.name) for u in User.query.filter_by(is_active=True).all()]
    
    if request.method == 'POST':
        if new_activity_form.validate_on_submit():
            try:
                # Verificar se a data de entrega é no passado
                hoje = datetime.now().date()
                status_inicial = 'in_progress'
                if new_activity_form.delivery_date.data and new_activity_form.delivery_date.data < hoje:
                    status_inicial = 'overdue'
                
                activity = Activity(
                    title=new_activity_form.title.data,
                    description=new_activity_form.description.data,
                    property_id=new_activity_form.property.data,
                    responsible_id=new_activity_form.responsible.data,
                    delivery_date=new_activity_form.delivery_date.data,
                    status=status_inicial,
                    created_by_id=current_user.id
                )
                db.session.add(activity)
                
                # Send informative message to responsible
                from app.models.message import Message
                msg = Message(
                    receiver_id=new_activity_form.responsible.data,
                    sender_id=current_user.id,
                    subject='Nova atividade atribuída',
                    body=f'{current_user.name} criou uma nova atividade para você: {new_activity_form.title.data}',
                    read=False
                )
                db.session.add(msg)
                
                # Se a propriedade tem um supervisor, também envia notificação para ele
                property_obj = Property.query.get(new_activity_form.property.data)
                if property_obj and property_obj.supervisor_id and property_obj.supervisor_id != current_user.id:
                    msg_supervisor = Message(
                        receiver_id=property_obj.supervisor_id,
                        sender_id=current_user.id,
                        subject='Nova atividade criada',
                        body=f'{current_user.name} criou uma nova atividade "{new_activity_form.title.data}" para {User.query.get(new_activity_form.responsible.data).name} no condomínio {property_obj.name}.',
                        read=False
                    )
                    db.session.add(msg_supervisor)
                
                db.session.commit()
                flash('Atividade criada com sucesso', 'success')
                return redirect(url_for('activity.list'))
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao criar atividade: {str(e)}', 'danger')
        else:
            for field, errors in new_activity_form.errors.items():
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
        
        if status and status not in ['pending', 'in_progress', 'completed', 'correction', 'not_completed', 'overdue', 'done', 'cancelled']:
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
        
        # Envia mensagem ao criador da atividade
        from app.models.message import Message
        if activity.created_by_id and activity.created_by_id != current_user.id:
            msg = Message(
                receiver_id=activity.created_by_id,
                sender_id=current_user.id,
                subject='Atividade enviada para verificação',
                body=f'{current_user.name} enviou a atividade "{activity.title}" para verificação.',
                read=False
            )
            db.session.add(msg)
        
        # Se quem concluiu foi um supervisor, também envia notificação para o responsável
        if current_user.role == 'supervisor' and activity.responsible_id != current_user.id:
            msg_responsavel = Message(
                receiver_id=activity.responsible_id,
                sender_id=current_user.id,
                subject='Atividade concluída por supervisor',
                body=f'{current_user.name} (supervisor) concluiu a atividade "{activity.title}" e enviou para verificação.',
                read=False
            )
            db.session.add(msg_responsavel)
        
        db.session.commit()
        flash('Atividade marcada como EM VERIFICAÇÃO!', 'success')
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

@activity.route('/import', methods=['GET', 'POST'])
@login_required
def import_activities():
    """Página para importar atividades via Excel"""
    if not (current_user.is_admin or current_user.is_supervisor):
        flash('Você não tem permissão para importar atividades', 'danger')
        return redirect(url_for('main.home'))
    
    form = ImportActivitiesForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            # Salva o arquivo temporariamente
            file = form.excel_file.data
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                file.save(tmp_file.name)
                tmp_file_path = tmp_file.name
            
            # Processa a importação
            importer = ActivityExcelImporter()
            success = importer.import_activities(tmp_file_path, current_user.id)
            summary = importer.get_summary()
            
            # Remove o arquivo temporário
            os.unlink(tmp_file_path)
            
            if success and summary['success_count'] > 0:
                flash(f'Importação concluída! {summary["success_count"]} atividades importadas com sucesso.', 'success')
                if summary['error_count'] > 0:
                    flash(f'{summary["error_count"]} linhas com erro. Verifique os detalhes abaixo.', 'warning')
            else:
                flash('Nenhuma atividade foi importada. Verifique os erros abaixo.', 'danger')
            
            return render_template('activity/import_result.html', summary=summary)
            
        except Exception as e:
            flash(f'Erro durante a importação: {str(e)}', 'danger')
    
    return render_template('activity/import.html', form=form)

@activity.route('/import/template')
@login_required
def download_template():
    """Download do template Excel para importação"""
    if not (current_user.is_admin or current_user.is_supervisor):
        flash('Você não tem permissão para baixar o template', 'danger')
        return redirect(url_for('main.home'))
    
    try:
        importer = ActivityExcelImporter()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            template_path = importer.create_template_excel(tmp_file.name)
        
        return send_file(
            template_path,
            as_attachment=True,
            download_name='template_importacao_atividades.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        flash(f'Erro ao gerar template: {str(e)}', 'danger')
        return redirect(url_for('activity.import_activities')) 