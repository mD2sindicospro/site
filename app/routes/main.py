from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, send_file, current_app
from flask_login import login_required, current_user
from app.forms.activity import NewActivityForm
from app.models.property import Property
from app.models.user import User
from app.models.activity import Activity
from datetime import datetime, timedelta
from app.extensions import db
from app.models.message import Message
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import xlsxwriter

main = Blueprint('main', __name__)

def prazo_humano(data_inicio, data_fim):
    if not data_inicio or not data_fim:
        return '—'
    delta = data_fim - data_inicio
    dias = delta.days
    segundos = delta.seconds
    if dias >= 30:
        meses = dias // 30
        return f"{meses}m"
    elif dias >= 1:
        return f"{dias}d"
    elif segundos >= 3600:
        horas = segundos // 3600
        return f"{horas}h"
    elif segundos >= 60:
        minutos = segundos // 60
        return f"{minutos}min"
    else:
        return f"{segundos}s"

def serialize_activity(activity):
    """Serialize activity for JSON response"""
    return {
        'id': activity.id,
        'title': activity.title,
        'description': activity.description,
        'status': activity.status,
        'priority': activity.priority,
        'property': activity.property.name if activity.property else None,
        'responsible': activity.responsible.name if activity.responsible else None,
        'created_at': activity.created_at.strftime('%d/%m/%Y %H:%M'),
        'updated_at': activity.updated_at.strftime('%d/%m/%Y %H:%M') if activity.updated_at else None,
        'delivery_date': activity.delivery_date.strftime('%d/%m/%Y') if activity.delivery_date else None
    }

@main.route('/')
@login_required
def home():
    # Get current page from query string
    current_page = request.args.get('page', 1, type=int)
    per_page = 20

    # Get activities based on user role
    if current_user.role == 'admin':
        query = Activity.query
    elif current_user.role == 'supervisor':
        query = Activity.query.join(Property).filter(Property.supervisor_id == current_user.id)
    else:
        query = Activity.query.filter_by(responsible_id=current_user.id)

    # Calculate total pages
    total_activities = query.count()
    total_pages = (total_activities + per_page - 1) // per_page

    # Get activities for current page
    activities = query.order_by(Activity.created_at.desc())\
        .offset((current_page - 1) * per_page)\
        .limit(per_page)\
        .all()

    # Create form for new activity
    form = NewActivityForm()
    form.property.choices = [(p.id, p.name) for p in Property.query.filter_by(is_active=True).all()]
    form.responsible.choices = [(u.id, u.name) for u in User.query.filter_by(is_active=True).all()]

    return render_template('main/home.html',
                         activities=activities,
                         total_paginas=total_pages,
                         current_page=current_page,
                         form=form)

@main.route('/home', methods=['GET', 'POST'])
@login_required
def home_post():
    if request.method == 'POST':
        form = NewActivityForm()
        form.property.choices = [(p.id, p.name) for p in Property.query.filter_by(is_active=True).all()]
        form.responsible.choices = [(u.id, u.name) for u in User.query.filter_by(is_active=True).all()]

        if form.validate_on_submit():
            try:
                activity = Activity(
                    property_id=form.property.data,
                    responsible_id=form.responsible.data,
                    created_by_id=current_user.id,
                    title=form.title.data,
                    description=form.description.data,
                    delivery_date=form.delivery_date.data,
                    resolved=False,
                    status='pending'
                )
                db.session.add(activity)
                # Send informative message to responsible
                msg = Message(
                    receiver_id=form.responsible.data,
                    sender_id=current_user.id,
                    subject='Nova atividade atribuída',
                    body=f'{current_user.name} criou uma nova atividade para você: {form.title.data}',
                    read=False
                )
                db.session.add(msg)
                db.session.commit()
                current_app.logger.info(f'Atividade criada com sucesso por {current_user.name}')
                flash('Atividade criada com sucesso!', 'success')
            except Exception as e:
                current_app.logger.error(f'Erro ao criar atividade: {str(e)}')
                db.session.rollback()
                flash('Erro ao criar atividade. Tente novamente.', 'danger')
            return redirect(url_for('main.home'))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    current_app.logger.warning(f'Erro de validação no campo {field}: {error}')
                    flash(f'Erro no campo {field}: {error}', 'danger')
            return redirect(url_for('main.home'))

    # Pagination of activities
    page = request.args.get('page', 1, type=int)
    per_page = 20
    activities_query = Activity.query.order_by(Activity.created_at.desc())
    total_activities = activities_query.count()
    total_pages = (total_activities + per_page - 1) // per_page
    activities = activities_query.offset((page - 1) * per_page).limit(per_page).all()

    # Add completion_date and status_color for each activity
    for a in activities:
        a.completion_date = getattr(a, 'completion_date', None)
        if a.resolved and not a.completion_date:
            a.completion_date = a.delivery_date
        hoje = datetime.now().date()
        if hasattr(a, 'status') and a.status == 'completed':
            a.status_color = 'primary'
        elif hasattr(a, 'status') and a.status == 'completed':
            a.status_color = 'success'
        elif hasattr(a, 'status') and a.status == 'in_progress':
            a.status_color = 'warning'
        elif hasattr(a, 'status') and a.status == 'overdue':
            a.status_color = 'info'
        elif hasattr(a, 'status') and a.status == 'overdue':
            a.status_color = 'danger'
        elif hasattr(a, 'status') and a.status == 'not_completed':
            a.status_color = 'secondary'
        elif hasattr(a, 'status') and a.status == 'correction':
            a.status_color = 'warning'
        else:
            a.status_color = 'secondary'

    # Cálculo dos percentuais para usuário normal ou supervisor
    percent_pending = percent_in_progress = percent_completed = percent_overdue = percent_not_completed = 0
    total_properties_supervisor = 0
    if current_user.role == 'user':
        properties_ativos = Property.query.filter_by(is_active=True).all()
        active_ids = [p.id for p in properties_ativos]
        activities_user = Activity.query.filter(Activity.responsible_id == current_user.id, Activity.property_id.in_(active_ids)).all()
        total_user = len(activities_user)
        if total_user > 0:
            percent_pending = round(len([a for a in activities_user if a.status == 'pending']) / total_user * 100)
            percent_in_progress = round(len([a for a in activities_user if a.status == 'in_progress']) / total_user * 100)
            percent_completed = round(len([a for a in activities_user if a.status == 'completed']) / total_user * 100)
            percent_overdue = round(len([a for a in activities_user if a.status == 'overdue']) / total_user * 100)
            percent_not_completed = round(len([a for a in activities_user if a.status == 'not_completed']) / total_user * 100)
    elif current_user.role == 'supervisor':
        properties_ativos = Property.query.filter_by(supervisor_id=current_user.id, is_active=True).all()
        total_properties_supervisor = len(properties_ativos)
        active_ids = [p.id for p in properties_ativos]
        activities_supervisor = Activity.query.filter(Activity.property_id.in_(active_ids)).all()
        total_supervisor = len(activities_supervisor)
        if total_supervisor > 0:
            percent_pending = round(len([a for a in activities_supervisor if a.status == 'pending']) / total_supervisor * 100)
            percent_in_progress = round(len([a for a in activities_supervisor if a.status == 'in_progress']) / total_supervisor * 100)
            percent_completed = round(len([a for a in activities_supervisor if a.status == 'completed']) / total_supervisor * 100)
            percent_overdue = round(len([a for a in activities_supervisor if a.status == 'overdue']) / total_supervisor * 100)
            percent_not_completed = round(len([a for a in activities_supervisor if a.status == 'not_completed']) / total_supervisor * 100)

    return render_template('main/home.html',
                         activities=activities,
        total_paginas=total_pages,
                         page=page,
        percent_pending=percent_pending,
        percent_in_progress=percent_in_progress,
        percent_completed=percent_completed,
        percent_overdue=percent_overdue,
        percent_not_completed=percent_not_completed,
                         total_properties_supervisor=total_properties_supervisor)

@main.route('/minhas-atividades')
@login_required
def my_activities():
    # Atualiza status para 'overdue' se vencido
    hoje = datetime.now().date()
    pending_activities = Activity.query.filter(
        Activity.responsible_id == current_user.id,
        Activity.status == 'pending',
        Activity.delivery_date < hoje
    ).all()
    for act in pending_activities:
        act.status = 'overdue'
    if pending_activities:
        db.session.commit()

    form = NewActivityForm()
    properties = Property.query.filter_by(is_active=True).all()
    form.property.choices = [(c.id, c.name) for c in properties]
    users = User.query.filter_by(is_active=True).all()
    form.responsible.choices = [(u.id, u.name) for u in users]

    # Filtros
    filter_property = request.args.get('property', type=int)
    filter_status = request.args.get('status', type=str)

    page = request.args.get('page', 1, type=int)
    per_page = 20
    activities_query = Activity.query.filter(
        Activity.responsible_id == current_user.id,
        Activity.status.notin_(['not_completed', 'completed'])
    )
    if filter_property:
        activities_query = activities_query.filter(Activity.property_id == filter_property)
    if filter_status:
        activities_query = activities_query.filter(Activity.status == filter_status)
    activities_query = activities_query.order_by(Activity.created_at.desc())
    total_activities = activities_query.count()
    total_pages = (total_activities + per_page - 1) // per_page
    activities = activities_query.offset((page - 1) * per_page).limit(per_page).all()

    for a in activities:
        a.completion_date = getattr(a, 'completion_date', None)
        if a.resolved and not a.completion_date:
            a.completion_date = a.delivery_date
        hoje = datetime.now().date()
        if hasattr(a, 'status') and a.status == 'completed':
            a.status_color = 'primary'
        elif hasattr(a, 'status') and a.status == 'completed':
            a.status_color = 'success'
        elif hasattr(a, 'status') and a.status == 'in_progress':
            a.status_color = 'warning'
        elif hasattr(a, 'status') and a.status == 'overdue':
            a.status_color = 'info'
        elif hasattr(a, 'status') and a.status == 'overdue':
            a.status_color = 'danger'
        elif hasattr(a, 'status') and a.status == 'not_completed':
            a.status_color = 'secondary'
        elif hasattr(a, 'status') and a.status == 'correction':
            a.status_color = 'warning'
        else:
            a.status_color = 'secondary'

    return render_template(
        'main/my_activities.html',
        title='Minhas Atividades',
        form=form,
        activities=activities,
        total_pages=total_pages,
        current_page=page,
        prazo_humano=prazo_humano,
        current_date=datetime.now().date()
    )

@main.route('/atividade/<int:atividade_id>/aceitar', methods=['POST'])
@login_required
def aceitar_atividade(atividade_id):
    atividade = Activity.query.get_or_404(atividade_id)
    if atividade.responsible_id != current_user.id:
        abort(403)
    if atividade.status in ['pending', 'correction']:
        atividade.status = 'in_progress'
        db.session.commit()
        flash('Atividade aceita com sucesso!', 'success')
    elif atividade.status == 'overdue':
        flash('Atividade aceita, mas permanece como vencida.', 'warning')
    return redirect(url_for('main.my_activities'))

@main.route('/atividade/<int:atividade_id>/concluir', methods=['POST'])
@login_required
def concluir_atividade(atividade_id):
    atividade = Activity.query.get_or_404(atividade_id)
    if atividade.responsible_id != current_user.id:
        current_app.logger.warning(f'Usuário {current_user.name} tentou concluir atividade de outro usuário')
        abort(403)
    
    try:
        atividade.status = 'completed'
        atividade.resolved = True
        atividade.completion_date = datetime.now()
        db.session.commit()
        current_app.logger.info(f'Atividade {atividade_id} concluída por {current_user.name}')
        flash('Atividade concluída com sucesso!', 'success')
    except Exception as e:
        current_app.logger.error(f'Erro ao concluir atividade {atividade_id}: {str(e)}')
        db.session.rollback()
        flash('Erro ao concluir atividade. Tente novamente.', 'danger')
    
    return redirect(url_for('main.home'))

@main.route('/atividade/<int:atividade_id>/desistir', methods=['POST'])
@login_required
def desistir_atividade(atividade_id):
    atividade = Activity.query.get_or_404(atividade_id)
    if atividade.responsible_id != current_user.id:
        abort(403)
    if atividade.status in ['pending', 'in_progress']:
        cancellation_reason = request.form.get('cancellation_reason', '').strip()
        if not cancellation_reason:
            flash('É obrigatório informar o motivo do cancelamento.', 'danger')
            return redirect(url_for('main.my_activities'))
        atividade.status = 'not_completed'
        atividade.resolved = False
        atividade.cancellation_reason = cancellation_reason
        db.session.commit()
        # Mensagem para o criador
        msg = Message(
            receiver_id=atividade.created_by_id,
            sender_id=current_user.id,
            subject='Atividade cancelada',
            body=f'{current_user.name} cancelou uma atividade que você criou: {atividade.title}',
            read=False
        )
        db.session.add(msg)
        db.session.commit()
        flash('Atividade cancelada com sucesso.', 'warning')
    return redirect(url_for('main.my_activities'))

@main.route('/approvals')
@login_required
def approvals():
    if not hasattr(current_user, 'role') or current_user.role not in ['supervisor', 'admin']:
        abort(403)
    
    if current_user.role == 'supervisor':
        # Busca as propriedades onde o usuário é supervisor
        properties_ids = [p.id for p in current_user.properties]
        # Filtra atividades apenas das propriedades onde é supervisor
        atividades = Activity.query.filter(
            Activity.status == 'completed',
            Activity.property_id.in_(properties_ids)
        ).order_by(Activity.created_at.desc()).all()
    else:  # admin
        # Admin pode ver todas as atividades
        atividades = Activity.query.filter_by(status='completed').order_by(Activity.created_at.desc()).all()
    
    return render_template('main/approvals.html', atividades=atividades)

@main.route('/aprovar-atividade/<int:atividade_id>', methods=['POST'])
@login_required
def aprovar_atividade(atividade_id):
    if not hasattr(current_user, 'role') or current_user.role not in ['supervisor', 'admin']:
        abort(403)
    atividade = Activity.query.get_or_404(atividade_id)
    # Se for supervisor, não pode aprovar atividades criadas por supervisores
    if current_user.role == 'supervisor':
        if atividade.created_by and atividade.created_by.role == 'supervisor':
            flash('Apenas administradores podem aprovar atividades de supervisores.', 'danger')
            return redirect(url_for('main.approvals'))
        properties_ids = [p.id for p in current_user.properties]
        if atividade.property_id not in properties_ids:
            flash('Você não tem permissão para aprovar atividades desta propriedade.', 'danger')
            return redirect(url_for('main.approvals'))
    if atividade.status == 'completed':
        atividade.status = 'completed'
        atividade.resolved = True
        atividade.approved_by_id = current_user.id
        db.session.commit()
        # Mensagem para o responsável
        msg = Message(
            receiver_id=atividade.responsible_id,
            sender_id=current_user.id,
            subject='Atividade aprovada',
            body=f'{current_user.name} aprovou sua atividade: {atividade.title}',
            read=False
        )
        db.session.add(msg)
        db.session.commit()
        flash('Atividade aprovada com sucesso!', 'success')
    else:
        flash('Apenas atividades concluídas podem ser aprovadas.', 'danger')
    return redirect(url_for('main.approvals'))

@main.route('/recusar-atividade/<int:atividade_id>', methods=['POST'])
@login_required
def recusar_atividade(atividade_id):
    if not hasattr(current_user, 'role') or current_user.role not in ['supervisor', 'admin']:
        abort(403)
    atividade = Activity.query.get_or_404(atividade_id)
    # Se for supervisor, não pode recusar atividades criadas por supervisores
    if current_user.role == 'supervisor':
        if atividade.created_by and atividade.created_by.role == 'supervisor':
            flash('Apenas administradores podem recusar atividades de supervisores.', 'danger')
            return redirect(url_for('main.approvals'))
        properties_ids = [p.id for p in current_user.properties]
        if atividade.property_id not in properties_ids:
            flash('Você não tem permissão para recusar atividades desta propriedade.', 'danger')
            return redirect(url_for('main.approvals'))
    if atividade.status == 'completed':
        atividade.status = 'not_completed'
        atividade.resolved = False
        db.session.commit()
        flash('Atividade recusada com sucesso!', 'warning')
    else:
        flash('Apenas atividades concluídas podem ser recusadas.', 'danger')
    return redirect(url_for('main.approvals'))

@main.route('/archive')
@login_required
def archive():
    form = NewActivityForm()
    properties = Property.query.filter_by(is_active=True).all()
    form.property.choices = [(p.id, p.name) for p in properties]
    users = User.query.filter_by(is_active=True).all()
    form.responsible.choices = [(u.id, u.name) for u in users]

    page = request.args.get('page', 1, type=int)
    per_page = 20
    filtro_property = request.args.get('property', type=int)
    filtro_status = request.args.get('status', type=str)
    filtro_supervisor = request.args.get('supervisor', type=int)
    data_lancamento_inicio = request.args.get('data_lancamento_inicio')
    data_lancamento_fim = request.args.get('data_lancamento_fim')

    if current_user.role == 'supervisor':
        properties_ids = [p.id for p in current_user.properties]
        atividades_query = Activity.query.filter(
            Activity.property_id.in_(properties_ids),
            Activity.status.in_(['completed', 'not_completed'])
        )
    elif current_user.role == 'admin':
        atividades_query = Activity.query.filter(
            Activity.status.in_(['completed', 'not_completed'])
        )
    else:
        atividades_query = Activity.query.filter(
            Activity.responsible_id == current_user.id,
            Activity.status.in_(['completed', 'not_completed'])
        )

    if filtro_property:
        atividades_query = atividades_query.filter(Activity.property_id == filtro_property)
    if filtro_status:
        atividades_query = atividades_query.filter(Activity.status == filtro_status)
    if filtro_supervisor:
        atividades_query = atividades_query.join(Activity.property).filter(Property.supervisor_id == filtro_supervisor)
    if data_lancamento_inicio:
        try:
            data_inicio = datetime.strptime(data_lancamento_inicio, '%d/%m/%Y')
        except ValueError:
            data_inicio = datetime.strptime(data_lancamento_inicio, '%Y-%m-%d')
        atividades_query = atividades_query.filter(Activity.created_at >= data_inicio)
    if data_lancamento_fim:
        try:
            data_fim = datetime.strptime(data_lancamento_fim, '%d/%m/%Y') + timedelta(days=1)
        except ValueError:
            data_fim = datetime.strptime(data_lancamento_fim, '%Y-%m-%d') + timedelta(days=1)
        atividades_query = atividades_query.filter(Activity.created_at < data_fim)

    atividades_query = atividades_query.order_by(Activity.created_at.desc())
    total_activities = atividades_query.count()
    total_pages = (total_activities + per_page - 1) // per_page
    atividades = atividades_query.offset((page - 1) * per_page).limit(per_page).all()

    for a in atividades:
        a.completion_date = getattr(a, 'completion_date', None)
        if a.resolved and not a.completion_date:
            a.completion_date = a.delivery_date
        hoje = datetime.now().date()
        if hasattr(a, 'status') and a.status == 'completed':
            a.status_color = 'primary'
        elif hasattr(a, 'status') and a.status == 'completed':
            a.status_color = 'success'
        elif hasattr(a, 'status') and a.status == 'in_progress':
            a.status_color = 'warning'
        elif hasattr(a, 'status') and a.status == 'overdue':
            a.status_color = 'info'
        elif hasattr(a, 'status') and a.status == 'overdue':
            a.status_color = 'danger'
        elif hasattr(a, 'status') and a.status == 'not_completed':
            a.status_color = 'secondary'
        elif hasattr(a, 'status') and a.status == 'correction':
            a.status_color = 'warning'
        else:
            a.status_color = 'secondary'

    return render_template(
        'main/archive.html',
        title='Arquivo de Atividades',
        form=form,
        activities=atividades,
        total_pages=total_pages,
        current_page=page,
        prazo_humano=prazo_humano,
        current_date=datetime.now().date()
    )

@main.route('/updates')
@login_required
def updates():
    messages = (Message.query
        .filter_by(receiver_id=current_user.id)
        .order_by(Message.created_at.desc())
        .limit(30)
        .all())
    return render_template('main/updates.html', messages=messages, current_date=datetime.now().date())

@main.route('/atividade/<int:atividade_id>/solicitar-correcao', methods=['POST'])
@login_required
def solicitar_correcao_atividade(atividade_id):
    if not hasattr(current_user, 'role') or current_user.role not in ['supervisor', 'admin']:
        abort(403)
    atividade = Activity.query.get_or_404(atividade_id)
    # Se for supervisor, não pode solicitar correção de atividades criadas por supervisores
    if current_user.role == 'supervisor':
        if atividade.created_by and atividade.created_by.role == 'supervisor':
            flash('Apenas administradores podem solicitar correção de atividades de supervisores.', 'danger')
            return redirect(url_for('main.approvals'))
        properties_ids = [p.id for p in current_user.properties]
        if atividade.property_id not in properties_ids:
            flash('Você não tem permissão para solicitar correção desta atividade.', 'danger')
            return redirect(url_for('main.approvals'))
    if atividade.status == 'completed':
        motivo = request.form.get('motivo_correcao', '').strip()
        if not motivo:
            flash('É obrigatório informar o motivo da correção.', 'danger')
            return redirect(url_for('main.approvals'))
        atividade.status = 'correction'
        atividade.resolved = False
        atividade.motivo_correcao = motivo
        db.session.commit()
        # Mensagem para o responsável
        msg = Message(
            receiver_id=atividade.responsible_id,
            sender_id=current_user.id,
            subject='Correção solicitada na atividade',
            body=f'{current_user.name} solicitou correção na sua atividade: {atividade.title}. Motivo: {motivo}',
            read=False
        )
        db.session.add(msg)
        db.session.commit()
        flash('Correção solicitada com sucesso!', 'warning')
    else:
        flash('Apenas atividades concluídas podem ter correção solicitada.', 'danger')
    return redirect(url_for('main.approvals'))

@main.route('/atividades-supervisor')
@login_required
def supervisor_activities():
    if not hasattr(current_user, 'role') or current_user.role != 'supervisor':
        abort(403)
    properties_ids = [p.id for p in current_user.properties]
    filtro_property = request.args.get('property', type=int)
    filtro_status = request.args.get('status', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    atividades_query = Activity.query.filter(
        Activity.property_id.in_(properties_ids),
        Activity.status.notin_(['not_completed', 'completed'])
    )
    if filtro_property:
        atividades_query = atividades_query.filter(Activity.property_id == filtro_property)
    if filtro_status:
        atividades_query = atividades_query.filter(Activity.status == filtro_status)
    atividades_query = atividades_query.order_by(Activity.created_at.desc())
    total_activities = atividades_query.count()
    total_pages = (total_activities + per_page - 1) // per_page
    atividades = atividades_query.offset((page - 1) * per_page).limit(per_page).all()
    for a in atividades:
        a.completion_date = getattr(a, 'completion_date', None)
        if a.resolved and not a.completion_date:
            a.completion_date = a.delivery_date
        if hasattr(a, 'status') and a.status == 'completed':
            a.status_color = 'primary'
        elif hasattr(a, 'status') and a.status == 'completed':
            a.status_color = 'success'
        elif hasattr(a, 'status') and a.status == 'in_progress':
            a.status_color = 'warning'
        elif hasattr(a, 'status') and a.status == 'overdue':
            a.status_color = 'info'
        elif hasattr(a, 'status') and a.status == 'overdue':
            a.status_color = 'danger'
        elif hasattr(a, 'status') and a.status == 'not_completed':
            a.status_color = 'secondary'
        elif hasattr(a, 'status') and a.status == 'correction':
            a.status_color = 'warning'
        else:
            a.status_color = 'secondary'
    properties = current_user.properties
    return render_template(
        'main/supervisor_activities.html',
        title='Atividades dos Meus Condomínios',
        activities=atividades,
        properties=properties,
        total_pages=total_pages,
        current_page=page,
        filtro_property=filtro_property,
        filtro_status=filtro_status,
        prazo_humano=prazo_humano,
        current_date=datetime.now().date()
    )

@main.route('/exportar-excel')
@login_required
def exportar_excel():
    """Export activities to Excel"""
    try:
        # Get filter parameters
        status = request.args.get('status', '')
        priority = request.args.get('priority', '')
        property_id = request.args.get('property_id', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # Base query
        query = Activity.query
        
        # Apply filters
        if status:
            query = query.filter(Activity.status == status)
        if priority:
            query = query.filter(Activity.priority == priority)
        if property_id:
            query = query.filter(Activity.property_id == property_id)
        if start_date:
            query = query.filter(Activity.created_at >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(Activity.created_at <= datetime.strptime(end_date, '%Y-%m-%d'))
        
        # Get activities
        atividades = query.all()
        
        # Create Excel file
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()
        
        # Add headers
        headers = ['ID', 'Título', 'Descrição', 'Status', 'Prioridade', 'Condomínio', 'Responsável', 
                  'Data de Criação', 'Data de Atualização', 'Data de Entrega']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        # Add data
        for row, atividade in enumerate(atividades, start=1):
            data = [
                atividade.id,
                atividade.title,
                atividade.description,
                atividade.status,
                atividade.priority,
                atividade.property.name if atividade.property else None,
                atividade.responsible.name if atividade.responsible else None,
                atividade.created_at.strftime('%d/%m/%Y %H:%M'),
                atividade.updated_at.strftime('%d/%m/%Y %H:%M') if atividade.updated_at else None,
                atividade.delivery_date.strftime('%d/%m/%Y') if atividade.delivery_date else None
            ]
            for col, value in enumerate(data):
                worksheet.write(row, col, value)
        
        workbook.close()
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'atividades_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
    except Exception as e:
        current_app.logger.error(f"Error exporting activities: {str(e)}")
        flash('Erro ao exportar atividades. Por favor, tente novamente.', 'error')
        return redirect(url_for('main.home'))

@main.route('/reports')
@login_required
def reports():
    if not (current_user.is_supervisor or current_user.is_admin):
        abort(403)
    form = NewActivityForm()
    properties = Property.query.filter_by(is_active=True).all()
    form.property.choices = [(c.id, c.name) for c in properties]
    users = User.query.filter_by(is_active=True).all()
    form.responsible.choices = [(u.id, u.name) for u in users]

    # Totais globais para admin
    total_properties = Property.query.count() if current_user.is_admin else None
    total_usuarios = User.query.filter_by(is_active=True).count() if current_user.is_admin else None
    total_pending = total_in_progress = total_completed = total_overdue = total_not_completed = 0
    percent_pending = percent_in_progress = percent_completed = percent_overdue = percent_not_completed = 0
    if current_user.is_admin:
        properties_ativos = Property.query.filter_by(is_active=True).all()
        ids_ativos = [c.id for c in properties_ativos]
        total_properties_supervisor = len(ids_ativos)
        atividades_admin = Activity.query.filter(Activity.property_id.in_(ids_ativos)).all()
        total_admin = len(atividades_admin)
        if total_admin > 0:
            pending = sum(1 for a in atividades_admin if a.status == 'pending')
            in_progress = sum(1 for a in atividades_admin if a.status in ['in_progress', 'correction'])
            completed = sum(1 for a in atividades_admin if a.status in ['completed', 'completed'])
            overdue = sum(1 for a in atividades_admin if a.status == 'overdue')
            not_completed = sum(1 for a in atividades_admin if a.status == 'not_completed')
            percent_pending = round((pending / total_admin) * 100)
            percent_in_progress = round((in_progress / total_admin) * 100)
            percent_completed = round((completed / total_admin) * 100)
            percent_overdue = round((overdue / total_admin) * 100)
            percent_not_completed = round((not_completed / total_admin) * 100)

    # Obtém os filtros da query string
    filtro_property = request.args.get('property', type=int)
    filtro_status = request.args.get('status', type=str)
    filtro_supervisor = request.args.get('supervisor', type=int)
    data_lancamento_inicio = request.args.get('data_lancamento_inicio')
    data_lancamento_fim = request.args.get('data_lancamento_fim')

    # Para admin, busca todas as atividades das propriedades ativas
    if current_user.is_admin:
        properties_ativos = Property.query.filter_by(is_active=True).all()
        ids_ativos = [p.id for p in properties_ativos]
        atividades_query = Activity.query.filter(Activity.property_id.in_(ids_ativos))
    else:
        atividades_query = Activity.query.filter_by(created_by_id=current_user.id)

    # Aplica os filtros
    if filtro_property:
        atividades_query = atividades_query.filter(Activity.property_id == filtro_property)
    if filtro_status:
        atividades_query = atividades_query.filter(Activity.status == filtro_status)
    if filtro_supervisor:
        atividades_query = atividades_query.join(Activity.property).filter(Property.supervisor_id == filtro_supervisor)
    if data_lancamento_inicio:
        try:
            data_inicio = datetime.strptime(data_lancamento_inicio, '%d/%m/%Y')
        except ValueError:
            data_inicio = datetime.strptime(data_lancamento_inicio, '%Y-%m-%d')
        atividades_query = atividades_query.filter(Activity.created_at >= data_inicio)
    if data_lancamento_fim:
        try:
            data_fim = datetime.strptime(data_lancamento_fim, '%d/%m/%Y') + timedelta(days=1)
        except ValueError:
            data_fim = datetime.strptime(data_lancamento_fim, '%Y-%m-%d') + timedelta(days=1)
        atividades_query = atividades_query.filter(Activity.created_at < data_fim)

    # Busca as atividades filtradas
    atividades = atividades_query.all()

    if current_user.is_admin:
        # Responsáveis comuns
        responsaveis = User.query.filter_by(is_active=True, role='user').all()
        responsaveis_dict = {u.id: {
            'usuario': u,
                'pending': 0,
                'in_progress': 0,
                'overdue': 0,
                'completed': 0,
                'not_completed': 0,
                'tarefas': []
        } for u in responsaveis}
        # Supervisores
        supervisores = User.query.filter_by(is_active=True, role='supervisor').all()
        supervisores_dict = {u.id: {
            'usuario': u,
            'pending': 0,
            'in_progress': 0,
            'overdue': 0,
            'completed': 0,
            'not_completed': 0,
            'tarefas': [],
            'aguardando_aprovacao': 0
        } for u in supervisores}
        # Preenche os dados
        for a in atividades:
            if a.responsible_id in responsaveis_dict:
                if a.status == 'pending':
                    responsaveis_dict[a.responsible_id]['pending'] += 1
                elif a.status in ['in_progress', 'correction']:
                    responsaveis_dict[a.responsible_id]['in_progress'] += 1
                elif a.status == 'overdue':
                    responsaveis_dict[a.responsible_id]['overdue'] += 1
                elif a.status in ['completed', 'completed']:
                    responsaveis_dict[a.responsible_id]['completed'] += 1
                elif a.status == 'not_completed':
                    responsaveis_dict[a.responsible_id]['not_completed'] += 1
                responsaveis_dict[a.responsible_id]['tarefas'].append(serialize_activity(a))
            if a.created_by_id in supervisores_dict:
                if a.status == 'pending':
                    supervisores_dict[a.created_by_id]['pending'] += 1
                elif a.status in ['in_progress', 'correction']:
                    supervisores_dict[a.created_by_id]['in_progress'] += 1
                elif a.status == 'overdue':
                    supervisores_dict[a.created_by_id]['overdue'] += 1
                elif a.status in ['completed', 'completed']:
                    supervisores_dict[a.created_by_id]['completed'] += 1
                elif a.status == 'not_completed':
                    supervisores_dict[a.created_by_id]['not_completed'] += 1
                if a.status == 'completed':
                    supervisores_dict[a.created_by_id]['aguardando_aprovacao'] += 1
                supervisores_dict[a.created_by_id]['tarefas'].append(serialize_activity(a))
        # Serialização para os gráficos
        responsaveis_graficos = {}
        for uid, u in responsaveis_dict.items():
            responsaveis_graficos[uid] = {
                'usuario': {'id': u['usuario'].id, 'username': u['usuario'].name},
                'pending': u['pending'],
                'in_progress': u['in_progress'],
                'overdue': u['overdue'],
                'completed': u['completed'],
                'not_completed': u['not_completed'],
                'tarefas': u['tarefas']
            }
        supervisores_graficos = {}
        for uid, u in supervisores_dict.items():
            supervisores_graficos[uid] = {
                'usuario': {'id': u['usuario'].id, 'username': u['usuario'].name},
                'pending': u['pending'],
                'in_progress': u['in_progress'],
                'overdue': u['overdue'],
                'completed': u['completed'],
                'not_completed': u['not_completed'],
                'tarefas': u['tarefas'],
                'aguardando_aprovacao': u['aguardando_aprovacao']
            }
        return render_template(
            'main/reports.html',
            responsaveis_graficos=responsaveis_graficos,
            supervisores_graficos=supervisores_graficos,
            form=form,
            total_properties=total_properties,
            total_usuarios=total_usuarios,
            total_pending=total_pending,
            total_in_progress=total_in_progress,
            total_completed=total_completed,
            total_overdue=total_overdue,
            total_not_completed=total_not_completed,
            percent_pending=percent_pending,
            percent_in_progress=percent_in_progress,
            percent_completed=percent_completed,
            percent_overdue=percent_overdue,
            percent_not_completed=percent_not_completed
        )
    else:
        # Supervisor mantém lógica atual
        usuarios = {u.id: {
            'usuario': u,
            'pending': 0,
            'in_progress': 0,
            'overdue': 0,
            'completed': 0,
            'not_completed': 0,
            'tarefas': []
        } for u in users}
        for a in atividades:
            if a.responsible_id in usuarios:
                if a.status == 'pending':
                    usuarios[a.responsible_id]['pending'] += 1
                elif a.status in ['in_progress', 'correction']:
                    usuarios[a.responsible_id]['in_progress'] += 1
                elif a.status == 'overdue':
                    usuarios[a.responsible_id]['overdue'] += 1
                elif a.status in ['completed', 'completed']:
                    usuarios[a.responsible_id]['completed'] += 1
                elif a.status == 'not_completed':
                    usuarios[a.responsible_id]['not_completed'] += 1
                usuarios[a.responsible_id]['tarefas'].append(serialize_activity(a))
    usuarios_graficos = {}
    for uid, u in usuarios.items():
        usuarios_graficos[uid] = {
            'usuario': {'id': u['usuario'].id, 'username': u['usuario'].name},
            'pending': u['pending'],
            'in_progress': u['in_progress'],
            'overdue': u['overdue'],
            'completed': u['completed'],
            'not_completed': u['not_completed']
        }
    return render_template(
        'main/reports.html',
        usuarios=usuarios,
        usuarios_graficos=usuarios_graficos,
        form=form,
        total_properties=total_properties,
        total_usuarios=total_usuarios,
        total_pending=total_pending,
        total_in_progress=total_in_progress,
        total_completed=total_completed,
        total_overdue=total_overdue,
        total_not_completed=total_not_completed,
        percent_pending=percent_pending,
        percent_in_progress=percent_in_progress,
        percent_completed=percent_completed,
        percent_overdue=percent_overdue,
        percent_not_completed=percent_not_completed
    ) 

@main.route('/atividades-admin')
@login_required
def atividades_admin():
    if not current_user.is_admin():
        abort(403)
    properties = Property.query.filter_by(is_active=True).all()
    filtro_property = request.args.get('property', type=int)
    filtro_status = request.args.get('status', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    atividades_query = Activity.query.filter(
        Activity.property_id.in_([p.id for p in properties]),
        Activity.status.notin_(['not_completed', 'completed'])
    )
    if filtro_property:
        atividades_query = atividades_query.filter(Activity.property_id == filtro_property)
    if filtro_status:
        atividades_query = atividades_query.filter(Activity.status == filtro_status)
    atividades_query = atividades_query.order_by(Activity.created_at.desc())
    total_activities = atividades_query.count()
    total_pages = (total_activities + per_page - 1) // per_page
    atividades = atividades_query.offset((page - 1) * per_page).limit(per_page).all()
    return render_template(
        'main/supervisor_activities.html',
        title='Atividades de Todos os Condomínios',
        activities=atividades,
        properties=properties,
        total_pages=total_pages,
        current_page=page,
        filtro_property=filtro_property,
        filtro_status=filtro_status,
        prazo_humano=prazo_humano,
        current_date=datetime.now().date()
    ) 