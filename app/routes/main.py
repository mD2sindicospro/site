from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, send_file, current_app, jsonify
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
from app.utils.translations import translate_status, get_status_class
from collections import OrderedDict
import io
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from unidecode import unidecode
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
import os
# import psutil  # Temporarily disabled

main = Blueprint('main', __name__)

@main.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return render_template('main/landing.html')

# Health check routes - SEM AUTENTICAÇÃO
@main.route('/health')
def health_check():
    """
    Rota simples para health check do Render.
    Retorna status básico da aplicação sem verificar banco de dados.
    """
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'site-m2d',
            'version': '1.0.0'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@main.route('/health-db')
def health_check_db():
    """
    Rota para verificar conexão com banco de dados.
    Usada para monitoramento mais detalhado.
    """
    try:
        # Teste simples de conexão com banco
        db.session.execute('SELECT 1')
        db.session.commit()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database_error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@main.route('/health-detailed')
def health_check_detailed():
    """
    Rota para health check detalhado (versão simplificada).
    """
    try:
        # Teste de banco de dados
        db_status = 'connected'
        try:
            db.session.execute('SELECT 1')
            db.session.commit()
        except Exception as e:
            db_status = f'error: {str(e)}'
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': db_status,
            'environment': os.getenv('FLASK_ENV', 'development'),
            'note': 'psutil temporarily disabled'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

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
        'atividade': activity.title,
        'description': activity.description,
        'status': activity.status,
        'property': {'id': activity.property.id, 'nome': activity.property.name} if activity.property else None,
        'responsavel': {'id': activity.responsible.id, 'username': activity.responsible.name} if activity.responsible else None,
        'data_lancamento': activity.created_at.strftime('%d/%m/%Y') if activity.created_at else '',
        'data_entrega': activity.delivery_date.strftime('%d/%m/%Y') if activity.delivery_date else '',
        'correction_reason': getattr(activity, 'correction_reason', None),
        'cancellation_reason': getattr(activity, 'cancellation_reason', None),
    }

@main.route('/home')
@login_required
def home():
    # Get activities based on user role
    if current_user.role == 'admin':
        query = Activity.query
    elif current_user.role == 'supervisor':
        # Supervisores veem todas as atividades (não apenas das propriedades que supervisionam)
        query = Activity.query
    else:
        query = Activity.query.filter_by(responsible_id=current_user.id)

    # Get only the 5 most recent activities (no pagination)
    activities = query.order_by(Activity.created_at.desc()).limit(5).all()

    # Buscar as 5 últimas notificações do usuário
    notifications = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.created_at.desc()).limit(5).all()

    # Create form for new activity
    new_activity_form = NewActivityForm()
    new_activity_form.property.choices = [(p.id, p.name) for p in Property.query.filter_by(is_active=True).all()]
    new_activity_form.responsible.choices = [(u.id, u.name) for u in User.query.filter_by(is_active=True).all()]

    # Cálculo dos percentuais para usuário normal, supervisor e admin
    percent_pending = percent_in_progress = percent_completed = percent_overdue = percent_not_completed = percent_cancelled = 0
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
            percent_cancelled = round(len([a for a in activities_user if a.status == 'cancelled']) / total_user * 100)
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
            percent_cancelled = round(len([a for a in activities_supervisor if a.status == 'cancelled']) / total_supervisor * 100)
    elif current_user.role == 'admin':
        activities_admin = Activity.query.all()
        total_admin = len(activities_admin)
        if total_admin > 0:
            percent_pending = round(len([a for a in activities_admin if a.status == 'pending']) / total_admin * 100)
            percent_in_progress = round(len([a for a in activities_admin if a.status == 'in_progress']) / total_admin * 100)
            percent_completed = round(len([a for a in activities_admin if a.status == 'completed']) / total_admin * 100)
            percent_overdue = round(len([a for a in activities_admin if a.status == 'overdue']) / total_admin * 100)
            percent_not_completed = round(len([a for a in activities_admin if a.status == 'not_completed']) / total_admin * 100)
            percent_cancelled = round(len([a for a in activities_admin if a.status == 'cancelled']) / total_admin * 100)

    return render_template('main/home.html',
                         activities=activities,
                         current_date=datetime.now().date(),
                         prazo_humano=prazo_humano,
                         percentual_pendentes=percent_pending,
                         percentual_andamento=percent_in_progress,
                         percentual_concluidas=percent_completed,
                         percentual_atrasadas=percent_overdue,
                         percentual_nao_realizadas=percent_not_completed,
                         percentual_canceladas=percent_cancelled,
                         total_properties_supervisor=total_properties_supervisor,
                         translate_status=translate_status,
                         get_status_class=get_status_class,
                         notifications=notifications,
                         new_activity_form=new_activity_form)

@main.route('/home', methods=['GET', 'POST'])
@login_required
def home_post():
    if request.method == 'POST':
        new_activity_form = NewActivityForm()
        new_activity_form.property.choices = [(p.id, p.name) for p in Property.query.filter_by(is_active=True).all()]
        new_activity_form.responsible.choices = [(u.id, u.name) for u in User.query.filter_by(is_active=True).all()]

        if new_activity_form.validate_on_submit():
            try:
                # Verificar se a data de entrega é no passado
                hoje = datetime.now().date()
                status_inicial = 'in_progress'
                if new_activity_form.delivery_date.data and new_activity_form.delivery_date.data < hoje:
                    status_inicial = 'overdue'
                
                activity = Activity(
                    property_id=new_activity_form.property.data,
                    responsible_id=new_activity_form.responsible.data,
                    created_by_id=current_user.id,
                    title=new_activity_form.title.data,
                    description=new_activity_form.description.data,
                    delivery_date=new_activity_form.delivery_date.data,
                    resolved=False,
                    status=status_inicial
                )
                db.session.add(activity)
                # Send informative message to responsible
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
                current_app.logger.info(f'Atividade criada com sucesso por {current_user.name}')
                flash('Atividade criada com sucesso!', 'success')
            except Exception as e:
                current_app.logger.error(f'Erro ao criar atividade: {str(e)}')
                db.session.rollback()
                flash('Erro ao criar atividade. Tente novamente.', 'danger')
            return redirect(url_for('main.home'))
        else:
            for field, errors in new_activity_form.errors.items():
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

    # Buscar as 5 últimas notificações do usuário
    notifications = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.created_at.desc()).limit(5).all()

    # Create form for new activity
    new_activity_form = NewActivityForm()
    new_activity_form.property.choices = [(p.id, p.name) for p in Property.query.filter_by(is_active=True).all()]
    new_activity_form.responsible.choices = [(u.id, u.name) for u in User.query.filter_by(is_active=True).all()]

    # Add completion_date and status_color for each activity
    for a in activities:
        a.completion_date = getattr(a, 'completion_date', None)
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

    # Cálculo dos percentuais para usuário normal, supervisor e admin
    percent_pending = percent_in_progress = percent_completed = percent_overdue = percent_not_completed = percent_cancelled = 0
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
            percent_cancelled = round(len([a for a in activities_user if a.status == 'cancelled']) / total_user * 100)
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
            percent_cancelled = round(len([a for a in activities_supervisor if a.status == 'cancelled']) / total_supervisor * 100)
    elif current_user.role == 'admin':
        activities_admin = Activity.query.all()
        total_admin = len(activities_admin)
        if total_admin > 0:
            percent_pending = round(len([a for a in activities_admin if a.status == 'pending']) / total_admin * 100)
            percent_in_progress = round(len([a for a in activities_admin if a.status == 'in_progress']) / total_admin * 100)
            percent_completed = round(len([a for a in activities_admin if a.status == 'completed']) / total_admin * 100)
            percent_overdue = round(len([a for a in activities_admin if a.status == 'overdue']) / total_admin * 100)
            percent_not_completed = round(len([a for a in activities_admin if a.status == 'not_completed']) / total_admin * 100)
            percent_cancelled = round(len([a for a in activities_admin if a.status == 'cancelled']) / total_admin * 100)

    return render_template('main/home.html',
                         activities=activities,
                         total_paginas=total_pages,
                         pagina_atual=page,
                         percentual_pendentes=percent_pending,
                         percentual_andamento=percent_in_progress,
                         percentual_concluidas=percent_completed,
                         percentual_atrasadas=percent_overdue,
                         percentual_nao_realizadas=percent_not_completed,
                         percentual_canceladas=percent_cancelled,
                         total_properties_supervisor=total_properties_supervisor,
                         current_date=datetime.now().date(),
                         prazo_humano=prazo_humano,
                         translate_status=translate_status,
                         get_status_class=get_status_class,
                         notifications=notifications,
                         new_activity_form=new_activity_form)

@main.route('/minhas-atividades')
@login_required
def my_activities():
    # Atualiza status para 'overdue' se vencido
    hoje = datetime.now().date()
    overdue_activities = Activity.query.filter(
        Activity.responsible_id == current_user.id,
        Activity.status == 'in_progress',
        Activity.delivery_date < hoje
    ).all()
    for act in overdue_activities:
        act.status = 'overdue'
    if overdue_activities:
        db.session.commit()

    new_activity_form = NewActivityForm()
    properties = Property.query.filter_by(is_active=True).all()
    new_activity_form.property.choices = [(c.id, c.name) for c in properties]
    users = User.query.filter_by(is_active=True).all()
    new_activity_form.responsible.choices = [(u.id, u.name) for u in users]

    # Filtros
    filter_property = request.args.get('property', type=int)
    filter_status = request.args.get('status', type=str)

    page = request.args.get('page', 1, type=int)
    per_page = 20
    if current_user.role == 'admin':
        activities_query = Activity.query.filter(
            Activity.status.notin_(['not_completed', 'cancelled', 'done', 'completed'])
        )
    elif current_user.role == 'supervisor':
        # Supervisores veem todas as atividades (não apenas das propriedades que supervisionam)
        activities_query = Activity.query.filter(
            Activity.status.notin_(['not_completed', 'cancelled', 'done', 'completed'])
        )
    else:
        activities_query = Activity.query.filter(
            Activity.responsible_id == current_user.id,
            Activity.status.notin_(['not_completed', 'cancelled', 'done', 'completed'])
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
        form=new_activity_form,
        activities=activities,
        total_pages=total_pages,
        current_page=page,
        prazo_humano=prazo_humano,
        current_date=datetime.now().date()
    )



@main.route('/atividade/<int:atividade_id>/concluir', methods=['POST'])
@login_required
def concluir_atividade(atividade_id):
    atividade = Activity.query.get_or_404(atividade_id)
    # Permite que responsável ou supervisor conclua a atividade
    if atividade.responsible_id != current_user.id and current_user.role != 'supervisor':
        current_app.logger.warning(f'Usuário {current_user.name} tentou concluir atividade de outro usuário')
        abort(403)
    
    try:
        atividade.status = 'completed'
        atividade.completion_date = datetime.now()
        db.session.commit()
        current_app.logger.info(f'Atividade {atividade_id} concluída por {current_user.name}')
        # Envia mensagem ao criador da atividade
        if atividade.created_by_id and atividade.created_by_id != current_user.id:
            msg = Message(
                receiver_id=atividade.created_by_id,
                sender_id=current_user.id,
                subject='Atividade enviada para verificação',
                body=f'{current_user.name} enviou a atividade "{atividade.title}" para verificação.',
                read=False
            )
            db.session.add(msg)
        
        # Se quem concluiu foi um supervisor, também envia notificação para o responsável
        if current_user.role == 'supervisor' and atividade.responsible_id != current_user.id:
            msg_responsavel = Message(
                receiver_id=atividade.responsible_id,
                sender_id=current_user.id,
                subject='Atividade concluída por supervisor',
                body=f'{current_user.name} (supervisor) concluiu a atividade "{atividade.title}" e enviou para verificação.',
                read=False
            )
            db.session.add(msg_responsavel)
        
            db.session.commit()
        flash('Atividade marcada como EM VERIFICAÇÃO!', 'success')
    except Exception as e:
        current_app.logger.error(f'Erro ao concluir atividade {atividade_id}: {str(e)}')
        db.session.rollback()
        flash('Erro ao concluir atividade. Tente novamente.', 'danger')
    
    return redirect(url_for('main.my_activities'))

@main.route('/atividade/<int:atividade_id>/desistir', methods=['POST'])
@login_required
def desistir_atividade(atividade_id):
    atividade = Activity.query.get_or_404(atividade_id)
    # Permite que responsável ou supervisor desista da atividade
    if atividade.responsible_id != current_user.id and current_user.role != 'supervisor':
        abort(403)
    if atividade.status in ['pending', 'in_progress']:
        cancellation_reason = request.form.get('cancellation_reason', '').strip()
        if not cancellation_reason:
            flash('É obrigatório informar o motivo do cancelamento.', 'danger')
            return redirect(url_for('main.my_activities'))
        atividade.status = 'cancelled'
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
        flash('Atividade cancelada com sucesso.', 'success')
    return redirect(url_for('main.my_activities'))

@main.route('/approvals')
@login_required
def approvals():
    # Apenas admins e supervisores podem aprovar atividades
    if not hasattr(current_user, 'role') or current_user.role not in ['admin', 'supervisor']:
        abort(403)
    
    # Admins veem todas as atividades em verificação
    atividades = Activity.query.filter_by(status='completed').order_by(Activity.created_at.desc()).all()
    
    return render_template(
        'main/approvals.html',
        atividades=atividades,
        prazo_humano=prazo_humano,
        current_date=datetime.now().date(),
        translate_status=translate_status,
        get_status_class=get_status_class
    )

@main.route('/aprovar-atividade/<int:atividade_id>', methods=['POST'])
@login_required
def aprovar_atividade(atividade_id):
    # Apenas admins e supervisores podem aprovar atividades
    if not hasattr(current_user, 'role') or current_user.role not in ['admin', 'supervisor']:
        abort(403)
    atividade = Activity.query.get_or_404(atividade_id)
    if atividade.status == 'completed':
        atividade.status = 'done'
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
        
        # Se a atividade tem um supervisor, também envia notificação para ele
        if atividade.property and atividade.property.supervisor_id:
            msg_supervisor = Message(
                receiver_id=atividade.property.supervisor_id,
                sender_id=current_user.id,
                subject='Atividade aprovada',
                body=f'{current_user.name} aprovou a atividade "{atividade.title}" que você supervisiona.',
                read=False
            )
            db.session.add(msg_supervisor)
        
        db.session.commit()
        flash('Atividade aprovada com sucesso!', 'success')
    else:
        flash('Apenas atividades EM VERIFICAÇÃO podem ser aprovadas.', 'danger')
    return redirect(url_for('main.approvals'))

@main.route('/recusar-atividade/<int:atividade_id>', methods=['POST'])
@login_required
def recusar_atividade(atividade_id):
    # Apenas admins e supervisores podem recusar atividades
    if not hasattr(current_user, 'role') or current_user.role not in ['admin', 'supervisor']:
        abort(403)
    atividade = Activity.query.get_or_404(atividade_id)
    if atividade.status == 'completed':
        motivo = request.form.get('rejection_reason', '').strip()
        if not motivo:
            flash('É obrigatório informar o motivo da recusa.', 'danger')
            return redirect(url_for('main.approvals'))
        atividade.status = 'not_completed'
        atividade.rejection_reason = motivo
        
        # Mensagem para o responsável
        msg = Message(
            receiver_id=atividade.responsible_id,
            sender_id=current_user.id,
            subject='Atividade recusada',
            body=f'{current_user.name} recusou sua atividade: {atividade.title}. Motivo: {motivo}',
            read=False
        )
        db.session.add(msg)
        
        # Se a atividade tem um supervisor, também envia notificação para ele
        if atividade.property and atividade.property.supervisor_id:
            msg_supervisor = Message(
                receiver_id=atividade.property.supervisor_id,
                sender_id=current_user.id,
                subject='Atividade recusada',
                body=f'{current_user.name} recusou a atividade "{atividade.title}" que você supervisiona. Motivo: {motivo}',
                read=False
            )
            db.session.add(msg_supervisor)
        
        db.session.commit()
        flash('Atividade recusada com sucesso!', 'warning')
    else:
        flash('Apenas atividades EM VERIFICAÇÃO podem ser recusadas.', 'danger')
    return redirect(url_for('main.approvals'))

@main.route('/archive')
@login_required
def archive():
    properties = Property.query.filter_by(is_active=True).all()
    new_activity_form = NewActivityForm()
    new_activity_form.property.choices = [(p.id, p.name) for p in properties]
    users = User.query.filter_by(is_active=True).all()
    new_activity_form.responsible.choices = [(u.id, u.name) for u in users]

    page = request.args.get('page', 1, type=int)
    per_page = 10
    filtro_property = request.args.get('property', type=int)
    filtro_status = request.args.get('status', type=str)
    filtro_supervisor = request.args.get('supervisor', type=int)
    data_lancamento_inicio = request.args.get('data_lancamento_inicio')
    data_lancamento_fim = request.args.get('data_lancamento_fim')

    if current_user.role == 'supervisor':
        # Supervisores veem todas as atividades arquivadas
        atividades_query = Activity.query.filter(
            Activity.status.in_(['done', 'not_completed', 'cancelled'])
        )
    elif current_user.role == 'admin':
        atividades_query = Activity.query.filter(
            Activity.status.in_(['done', 'not_completed', 'cancelled'])
        )
    else:
        atividades_query = Activity.query.filter(
            Activity.responsible_id == current_user.id,
            Activity.status.in_(['done', 'not_completed', 'cancelled'])
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

    # Filtro padrão: últimos 3 meses, a não ser que o usuário escolha outro período
    if not data_lancamento_inicio and not data_lancamento_fim and not current_user.is_admin:
        data_limite = datetime.now() - timedelta(days=90)
        atividades = [a for a in atividades if a.created_at and a.created_at >= data_limite]

    return render_template(
        'main/archive.html',
        title='Arquivo de Atividades',
        form=new_activity_form,
        activities=atividades,
        total_paginas=total_pages,
        pagina_atual=page,
        prazo_humano=prazo_humano,
        current_date=datetime.now().date(),
        translate_status=translate_status,
        get_status_class=get_status_class
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
    # Apenas admins e supervisores podem solicitar correção de atividades
    if not hasattr(current_user, 'role') or current_user.role not in ['admin', 'supervisor']:
        abort(403)
    atividade = Activity.query.get_or_404(atividade_id)
    if atividade.status == 'completed':
        motivo = request.form.get('motivo_correcao', '').strip()
        if not motivo:
            flash('É obrigatório informar o motivo da correção.', 'danger')
            return redirect(url_for('main.approvals'))
        atividade.status = 'correction'
        atividade.correction_reason = motivo
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
        
        # Se a atividade tem um supervisor, também envia notificação para ele
        if atividade.property and atividade.property.supervisor_id:
            msg_supervisor = Message(
                receiver_id=atividade.property.supervisor_id,
                sender_id=current_user.id,
                subject='Correção solicitada na atividade',
                body=f'{current_user.name} solicitou correção na atividade "{atividade.title}" que você supervisiona. Motivo: {motivo}',
                read=False
            )
            db.session.add(msg_supervisor)
        
        db.session.commit()
        flash('Correção solicitada com sucesso!', 'warning')
    else:
        flash('Apenas atividades EM VERIFICAÇÃO podem ter correção solicitada.', 'danger')
    return redirect(url_for('main.approvals'))

@main.route('/atividades-supervisor')
@login_required
def supervisor_activities():
    if not hasattr(current_user, 'role') or current_user.role != 'supervisor':
        abort(403)
    properties_ids = [p.id for p in current_user.properties_supervisionados]
    filtro_property = request.args.get('property', type=int)
    filtro_status = request.args.get('status', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    # Supervisores veem todas as atividades (não apenas das propriedades que supervisionam)
    atividades_query = Activity.query.filter(
        Activity.status.notin_(['not_completed', 'cancelled', 'done', 'completed'])
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

    properties = current_user.properties_supervisionados
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
        headers = ['ID', 'Título', 'Descrição', 'Status', 'Condomínio', 'Responsável', 
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
    properties = Property.query.filter_by(is_active=True).all()
    new_activity_form = NewActivityForm()
    new_activity_form.property.choices = [(c.id, c.name) for c in properties]
    users = User.query.filter_by(is_active=True).all()
    new_activity_form.responsible.choices = [(u.id, u.name) for u in users]

    # Totais globais para admin e supervisor
    total_properties = Property.query.count() if current_user.is_admin or current_user.is_supervisor else None
    total_usuarios = User.query.filter_by(is_active=True).count() if current_user.is_admin or current_user.is_supervisor else None
    total_pending = total_in_progress = total_completed = total_overdue = total_not_completed = 0
    percent_pending = percent_in_progress = percent_completed = percent_overdue = percent_not_completed = percent_cancelled = 0
    if current_user.is_admin or current_user.is_supervisor:
        properties_ativos = Property.query.filter_by(is_active=True).all()
        ids_ativos = [c.id for c in properties_ativos]
        total_properties_supervisor = len(ids_ativos)
        atividades_admin = Activity.query.filter(Activity.property_id.in_(ids_ativos)).all()
        total_admin = len(atividades_admin)
        if total_admin > 0:
            pending = sum(1 for a in atividades_admin if a.status == 'pending')
            in_progress = sum(1 for a in atividades_admin if a.status in ['in_progress', 'correction'])
            completed = sum(1 for a in atividades_admin if a.status == 'completed')
            overdue = sum(1 for a in atividades_admin if a.status == 'overdue')
            not_completed = sum(1 for a in atividades_admin if a.status == 'not_completed')
            cancelled = sum(1 for a in atividades_admin if a.status == 'cancelled')
            percent_pending = round((pending / total_admin) * 100)
            percent_in_progress = round((in_progress / total_admin) * 100)
            percent_completed = round((completed / total_admin) * 100)
            percent_overdue = round((overdue / total_admin) * 100)
            percent_not_completed = round((not_completed / total_admin) * 100)
            percent_cancelled = round((cancelled / total_admin) * 100)

    # Obtém os filtros da query string
    filtro_property = request.args.get('property', type=int)
    filtro_status = request.args.get('status', type=str)
    filtro_supervisor = request.args.get('supervisor', type=int)
    data_lancamento_inicio = request.args.get('data_lancamento_inicio')
    data_lancamento_fim = request.args.get('data_lancamento_fim')

    # Lógica de filtragem por tipo de usuário
    if current_user.is_admin:
        properties_ativos = Property.query.filter_by(is_active=True).all()
        ids_ativos = [p.id for p in properties_ativos]
        atividades_query = Activity.query.filter(Activity.property_id.in_(ids_ativos))
    elif current_user.is_supervisor:
        # Supervisores veem todas as atividades
        properties_ativos = Property.query.filter_by(is_active=True).all()
        ids_ativos = [p.id for p in properties_ativos]
        atividades_query = Activity.query.filter(Activity.property_id.in_(ids_ativos))
    else:
        activities_query = Activity.query.filter(
            Activity.responsible_id == current_user.id,
            Activity.status.notin_(['not_completed', 'cancelled'])
        )

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

    atividades = atividades_query.all()
    # Filtro padrão: últimos 3 meses, a não ser que o usuário escolha outro período
    if not data_lancamento_inicio and not data_lancamento_fim and not (current_user.is_admin or current_user.is_supervisor):
        data_limite = datetime.now() - timedelta(days=90)
        atividades = [a for a in atividades if a.created_at and a.created_at >= data_limite]

    if current_user.is_admin or current_user.is_supervisor:
        # Montagem dos gráficos de responsáveis (users)
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
        for a in atividades:
            if a.responsible_id and a.responsible_id in responsaveis_dict:
                if a.status == 'pending':
                    responsaveis_dict[a.responsible_id]['pending'] += 1
                elif a.status in ['in_progress', 'correction']:
                    responsaveis_dict[a.responsible_id]['in_progress'] += 1
                elif a.status == 'overdue':
                    responsaveis_dict[a.responsible_id]['overdue'] += 1
                elif a.status == 'completed':
                    responsaveis_dict[a.responsible_id]['completed'] += 1
                elif a.status == 'not_completed':
                    responsaveis_dict[a.responsible_id]['not_completed'] += 1
                responsaveis_dict[a.responsible_id]['tarefas'].append(serialize_activity(a))
        responsaveis_graficos = {}
        for uid, u in responsaveis_dict.items():
            responsaveis_graficos[uid] = {
                'usuario': {'id': u['usuario'].id, 'username': u['usuario'].name},
                'pending': u['pending'],
                'in_progress': u['in_progress'],
                'overdue': u['overdue'],
                'completed': u['completed'],
                'not_completed': u['not_completed'],
                'pendentes': u['pending'],
                'em_andamento': u['in_progress'],
                'atrasadas': u['overdue'],
                'concluidas': u['completed'],
                'em_verificacao': u['completed'],
                'nao_realizadas': u['not_completed'],
                'tarefas': u['tarefas']
            }
        # Montagem dos gráficos de supervisores
        supervisores = User.query.filter_by(is_active=True, role='supervisor').all()
        supervisores_dict = {}
        for supervisor in supervisores:
            cond_ids = [c.id for c in Property.query.filter_by(supervisor_id=supervisor.id, is_active=True).all()]
            atividades_sup = [a for a in atividades if a.property_id in cond_ids]
            supervisores_dict[supervisor.id] = {
                'usuario': supervisor,
                'pending': 0,
                'in_progress': 0,
                'overdue': 0,
                'completed': 0,
                'not_completed': 0,
                'tarefas': [],
                'aguardando_aprovacao': 0
            }
            for a in atividades_sup:
                if a.status == 'pending':
                    supervisores_dict[supervisor.id]['pending'] += 1
                elif a.status in ['in_progress', 'correction']:
                    supervisores_dict[supervisor.id]['in_progress'] += 1
                elif a.status == 'overdue':
                    supervisores_dict[supervisor.id]['overdue'] += 1
                elif a.status == 'completed':
                    supervisores_dict[supervisor.id]['completed'] += 1
                    supervisores_dict[supervisor.id]['aguardando_aprovacao'] += 1
                elif a.status == 'not_completed':
                    supervisores_dict[supervisor.id]['not_completed'] += 1
                supervisores_dict[supervisor.id]['tarefas'].append(serialize_activity(a))
        supervisores_graficos = {}
        for uid, u in supervisores_dict.items():
            supervisores_graficos[uid] = {
                'usuario': {'id': u['usuario'].id, 'username': u['usuario'].name},
                'pending': u['pending'],
                'in_progress': u['in_progress'],
                'overdue': u['overdue'],
                'completed': u['completed'],
                'not_completed': u['not_completed'],
                'pendentes': u['pending'],
                'em_andamento': u['in_progress'],
                'atrasadas': u['overdue'],
                'concluidas': u['completed'],
                'em_verificacao': u['completed'],
                'nao_realizadas': u['not_completed'],
                'tarefas': u['tarefas'],
                'aguardando_aprovacao': u['aguardando_aprovacao']
            }
        # PRODUTIVIDADE DIÁRIA
        if data_lancamento_inicio:
            data_inicio = datetime.strptime(data_lancamento_inicio, '%d/%m/%Y') if '/' in data_lancamento_inicio else datetime.strptime(data_lancamento_inicio, '%Y-%m-%d')
        else:
            data_inicio = (datetime.now() - timedelta(days=89)).replace(hour=0, minute=0, second=0, microsecond=0)
        if data_lancamento_fim:
            data_fim = datetime.strptime(data_lancamento_fim, '%d/%m/%Y') if '/' in data_lancamento_fim else datetime.strptime(data_lancamento_fim, '%Y-%m-%d')
        else:
            data_fim = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        dias = (data_fim - data_inicio).days + 1
        produtividade_diaria = OrderedDict()
        for i in range(dias):
            dia = (data_inicio + timedelta(days=i)).date()
            produtividade_diaria[dia.strftime('%d/%m/%Y')] = {'completed': 0, 'done': 0}
        for a in atividades:
            if a.status in ['completed', 'done'] and a.created_at:
                dia = a.created_at.date().strftime('%d/%m/%Y')
                if dia in produtividade_diaria:
                    produtividade_diaria[dia][a.status] += 1
        supervisores_status_grafico = {}
        for uid, u in responsaveis_graficos.items():
            supervisores_status_grafico[uid] = {
                'nome': u['usuario']['username'],
                'pendente': u.get('pendentes', 0),
                'em_andamento': u.get('em_andamento', 0),
                'atrasada': u.get('atrasadas', 0),
                'em_verificacao': u.get('em_verificacao', 0),
                'realizada': u.get('concluidas', 0),
                'nao_realizada': u.get('nao_realizadas', 0),
            }
        return render_template(
            'main/reports.html',
            responsaveis_graficos=responsaveis_graficos,
            supervisores_graficos=supervisores_graficos,
            supervisores_status_grafico=supervisores_status_grafico,
            produtividade_diaria=produtividade_diaria,
            form=new_activity_form,
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
            percent_not_completed=percent_not_completed,
            translate_status=translate_status,
            get_status_class=get_status_class
        )
    # Usuário comum
    atividades_por_supervisor = {}
    supervisores_status_grafico = {}
    for a in atividades:
        if a.created_by and a.created_by.role in ['supervisor', 'admin']:
            sup_id = a.created_by.id
            if sup_id not in atividades_por_supervisor:
                atividades_por_supervisor[sup_id] = {
                    'usuario': a.created_by,
                    'total': 0,
                    'tarefas': []
                }
            atividades_por_supervisor[sup_id]['total'] += 1
            atividades_por_supervisor[sup_id]['tarefas'].append(serialize_activity(a))
            # Contagem de status por supervisor
            if sup_id not in supervisores_status_grafico:
                supervisores_status_grafico[sup_id] = {
                    'nome': a.created_by.name,
                    'pendente': 0,
                    'em_andamento': 0,
                    'atrasada': 0,
                    'em_verificacao': 0,
                    'realizada': 0,
                    'aprovada': 0,
                    'nao_realizada': 0
                }
            if a.status == 'pending':
                supervisores_status_grafico[sup_id]['pendente'] += 1
            elif a.status in ['in_progress', 'correction']:
                supervisores_status_grafico[sup_id]['em_andamento'] += 1
            elif a.status == 'overdue':
                supervisores_status_grafico[sup_id]['atrasada'] += 1
            elif a.status == 'done':
                supervisores_status_grafico[sup_id]['realizada'] += 1
            elif a.status == 'completed':
                supervisores_status_grafico[sup_id]['em_verificacao'] += 1
            elif a.status == 'not_completed':
                supervisores_status_grafico[sup_id]['nao_realizada'] += 1
    supervisores_graficos = {}
    for uid, u in atividades_por_supervisor.items():
        supervisores_graficos[uid] = {
        'usuario': {'id': u['usuario'].id, 'username': u['usuario'].name},
            'total': u['total'],
            'pendentes': supervisores_status_grafico[uid]['pendente'],
            'em_andamento': supervisores_status_grafico[uid]['em_andamento'],
            'atrasadas': supervisores_status_grafico[uid]['atrasada'],
            'em_verificacao': supervisores_status_grafico[uid]['em_verificacao'],
            'nao_realizadas': supervisores_status_grafico[uid]['nao_realizada'],
        'tarefas': u['tarefas']
    }
    # PRODUTIVIDADE DIÁRIA (corrigido para sempre mostrar últimos 90 dias)
    if data_lancamento_inicio:
        data_inicio = datetime.strptime(data_lancamento_inicio, '%d/%m/%Y') if '/' in data_lancamento_inicio else datetime.strptime(data_lancamento_inicio, '%Y-%m-%d')
    else:
        data_inicio = (datetime.now() - timedelta(days=89)).replace(hour=0, minute=0, second=0, microsecond=0)
    if data_lancamento_fim:
        data_fim = datetime.strptime(data_lancamento_fim, '%d/%m/%Y') if '/' in data_lancamento_fim else datetime.strptime(data_lancamento_fim, '%Y-%m-%d')
    else:
        data_fim = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    dias = (data_fim - data_inicio).days + 1
    produtividade_diaria = OrderedDict()
    for i in range(dias):
        dia = (data_inicio + timedelta(days=i)).date()
        produtividade_diaria[dia.strftime('%d/%m/%Y')] = {'completed': 0, 'done': 0}
    for a in atividades:
        if a.status in ['completed', 'done'] and a.created_at:
            dia = a.created_at.date().strftime('%d/%m/%Y')
            if dia in produtividade_diaria:
                produtividade_diaria[dia][a.status] += 1
    return render_template(
        'main/reports.html',
        supervisores_graficos=supervisores_graficos,
        supervisores_status_grafico=supervisores_status_grafico,
        produtividade_diaria=produtividade_diaria,
        form=new_activity_form,
        total_properties=None,
        total_usuarios=None,
        total_pending=None,
        total_in_progress=None,
        total_completed=None,
        total_overdue=None,
        total_not_completed=None,
        percent_pending=None,
        percent_in_progress=None,
        percent_completed=None,
        percent_overdue=None,
        percent_not_completed=None,
        translate_status=translate_status,
        get_status_class=get_status_class
    )

@main.route('/atividades-admin')
@login_required
def atividades_admin():
    if not current_user.is_admin:
        abort(403)
    properties = Property.query.filter_by(is_active=True).all()
    filtro_property = request.args.get('property', type=int)
    filtro_status = request.args.get('status', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    atividades_query = Activity.query.filter(
        Activity.property_id.in_([p.id for p in properties]),
        Activity.status.notin_(['not_completed', 'cancelled', 'done', 'completed'])
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

@main.route('/exportar-pdf')
def exportar_pdf():
    from app.models.property import Property
    from app.models.user import User
    # Receber filtros
    property_id = request.args.get('property', type=int)
    data_inicio = request.args.get('data_lancamento_inicio')
    data_fim = request.args.get('data_lancamento_fim')
    status = request.args.getlist('status')

    # Filtro base: apenas status marcados no modal
    if status:
        # Se status foram marcados no modal, usar apenas eles
        print(f"=== DEBUG: Status filtrados: {status} ===")
        print(f"=== DEBUG: Tipos dos status: {[type(s) for s in status]} ===")
        print(f"=== DEBUG: Status 'not_completed' existe? {'not_completed' in status} ===")
        atividades_query = Activity.query.filter(Activity.status.in_(status))
        
        # Debug adicional: verificar quantas atividades existem com cada status
        for s in status:
            count = Activity.query.filter(Activity.status == s).count()
            print(f"=== DEBUG: Status '{s}' tem {count} atividades ===")
    else:
        # Se nenhum status foi marcado, não retornar nenhuma atividade
        # (força o usuário a selecionar pelo menos um status)
        print("=== DEBUG: Nenhum status selecionado ===")
        atividades_query = Activity.query.filter(Activity.id == 0)  # Query vazia
    
    if property_id:
        atividades_query = atividades_query.filter(Activity.property_id == property_id)
    if data_inicio:
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%d/%m/%Y')
        except ValueError:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
        atividades_query = atividades_query.filter(Activity.created_at >= data_inicio_dt)
    if data_fim:
        try:
            data_fim_dt = datetime.strptime(data_fim, '%d/%m/%Y') + timedelta(days=1)
        except ValueError:
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
        atividades_query = atividades_query.filter(Activity.created_at < data_fim_dt)
    atividades_query = atividades_query.order_by(Activity.created_at.desc())
    atividades = atividades_query.all()
    
    # Debug: verificar os status das atividades
    print("=== DEBUG: Status das atividades ===")
    print(f"Total de atividades encontradas: {len(atividades)}")
    print(f"Query SQL: {atividades_query}")
    for a in atividades:
        print(f"ID: {a.id}, Título: {a.title}, Status: {a.status}, Traduzido: {translate_status(a.status)}")
    print("=== FIM DEBUG ===")
    
    # Verificar se há dados para exportar
    if not atividades:
        flash('Nenhuma atividade encontrada com os filtros selecionados. Verifique os status, período ou condomínio escolhidos.', 'warning')
        return redirect(url_for('main.archive'))
    
    # Verificação adicional para garantir que há dados válidos
    if len(atividades) == 0:
        flash('Nenhuma atividade encontrada com os filtros selecionados. Verifique os status, período ou condomínio escolhidos.', 'warning')
        return redirect(url_for('main.archive'))

    # Nome do condomínio
    nome_condominio = 'Todos os Condomínios'
    logo_condominio_url = None
    if property_id:
        prop = Property.query.get(property_id)
        if prop:
            nome_condominio = prop.name
            logo_condominio_url = prop.logo_url

    # Gerar PDF com platypus em modo paisagem
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=1*cm, rightMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    # Definir cores da empresa (azul escuro)
    empresa_blue = colors.HexColor('#11141b')
    empresa_light_blue = colors.HexColor('#3498db')
    empresa_gray = colors.HexColor('#f8f9fa')
    
    # Estilos profissionais
    header_style = ParagraphStyle('header', parent=styles['Normal'], 
                                alignment=TA_CENTER, fontSize=14, fontName='Helvetica-Bold',
                                textColor=empresa_blue, spaceAfter=10)
    
    subtitle_style = ParagraphStyle('subtitle', parent=styles['Normal'],
                                  alignment=TA_RIGHT, fontSize=12, fontName='Helvetica',
                                  textColor=colors.grey, spaceAfter=8)
    
    company_style = ParagraphStyle('company', parent=styles['Normal'],
                                 alignment=TA_CENTER, fontSize=14, fontName='Helvetica-Bold',
                                 textColor=empresa_blue, spaceAfter=20)
    
    # Estilo para a logo alinhada
    logo_style = ParagraphStyle('logo', parent=styles['Normal'],
                               alignment=TA_LEFT, fontSize=12, fontName='Helvetica',
                               textColor=empresa_blue, spaceAfter=20, spaceBefore=10)
    
    # Função para criar cabeçalho fixo
    def create_header(canvas, doc):
        canvas.saveState()
        
        # Cabeçalho profissional com layout melhorado
        header_data = [
            [
                # Coluna esquerda - Logo MD2
                Paragraph('''
                    <para align="left">
                        <img src="app/static/images/logo.png" width="3.5cm" height="1.8cm" valign="middle"/>
                    </para>
                ''', logo_style),
                
                # Coluna central - Título, período e nome do condomínio com hierarquia visual
                Paragraph(f'''
                    <para align="center">
                        <font size="12" color="#1a1a1a"><b>RELATÓRIO DE ATIVIDADES</b></font><br/>
                        <font size="8" color="#666666">{f'Período: {data_inicio or "Início"} a {data_fim or "Atual"}' if data_inicio or data_fim else ''}</font><br/>
                        <font size="11" color="#2c3e50"><b>{nome_condominio}</b></font>
                    </para>
                ''', header_style),
                
                # Coluna direita - Logo do condomínio
                Paragraph(f'''
                    <para align="right">
                        {f'<img src="{logo_condominio_url}" width="3.5cm" height="1.8cm" valign="middle"/>' if logo_condominio_url else ''}
                    </para>
                ''', ParagraphStyle('footer', parent=styles['Normal'],
                                  alignment=TA_RIGHT, fontSize=8, fontName='Helvetica',
                                  textColor=colors.grey, rightIndent=0))
            ]
        ]
        header_table = Table(header_data, colWidths=[6*cm, 9*cm, 7*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ]))
        
        # Posicionar cabeçalho no topo da página
        header_table.wrapOn(canvas, doc.width, doc.height)
        # Centralizar o cabeçalho na página
        header_width = 22*cm  # Largura total do cabeçalho (6+9+7)
        header_x = (doc.width - header_width) / 2 + doc.leftMargin
        header_table.drawOn(canvas, header_x, doc.height + doc.topMargin - 2.5*cm)
        
        # Adicionar rodapé na mesma função
        footer_text = f'''
            <para align="center">
                <font size="8" color="#34495e"><b>MD2 SÍNDICOS PROFISSIONAIS</b></font><br/>
                <font size="6" color="#7f8c8d">Relatório gerado em: {datetime.now().strftime("%d/%m/%Y às %H:%M")}</font><br/>
                <font size="6" color="#7f8c8d">Emitido por: {current_user.name}</font>
            </para>
        '''
        footer_paragraph = Paragraph(footer_text, ParagraphStyle('footer_info', parent=styles['Normal'],
                                                               alignment=TA_CENTER, fontSize=8, fontName='Helvetica',
                                                               textColor=colors.grey))
        
        # Posicionar rodapé no final da página
        footer_paragraph.wrapOn(canvas, doc.width, doc.height)
        footer_paragraph.drawOn(canvas, doc.leftMargin, doc.bottomMargin + 1*cm)
        
        canvas.restoreState()
    
    # Adicionar espaço para o cabeçalho
    elements.append(Spacer(1, 4*cm))
    
    # Tabela principal com coluna de conclusão
    data = [[
        'Lançamento', 'Responsável', 'Título', 'Status', 'Conclusão'
    ]]
    observacoes = []
    for a in atividades:
        lancamento = a.created_at.strftime('%d/%m/%Y') if a.created_at else ''
        responsavel = a.responsible.name if a.responsible else ''
        titulo = a.title
        # Garantir que o status seja exatamente o do banco
        status_str = translate_status(a.status)
        # Debug adicional para verificar a tradução
        print(f"DEBUG PDF - ID: {a.id}, Status DB: {a.status}, Status Traduzido: {status_str}")
        print(f"DEBUG PDF - Status original: '{a.status}', Traduzido: '{status_str}'")
        motivo = a.cancellation_reason or ''
        print(f"=== DEBUG: Atividade '{titulo}' - Status: {a.status}, Motivo: '{motivo}' ===")
        # Data de conclusão - apenas para status 'done'
        conclusao = a.delivery_date.strftime('%d/%m/%Y') if a.status == 'done' and a.delivery_date else '—'
        data.append([lancamento, responsavel, titulo, status_str, conclusao])
        # Se for cancelada ou não realizada e tiver motivo, adiciona em observações
        if a.status in ['cancelled', 'not_completed'] and motivo:
            observacoes.append([titulo, status_str, motivo])
            print(f"=== DEBUG: Adicionando observação - Título: {titulo}, Status: {status_str}, Motivo: {motivo} ===")
    
    # Verificar se há dados além do cabeçalho
    if len(data) <= 1:  # Apenas cabeçalho
        flash('Nenhuma atividade encontrada com os filtros selecionados. Verifique os status, período ou condomínio escolhidos.', 'warning')
        return redirect(url_for('main.archive'))
    
    # Verificação final antes de criar a tabela
    if not data or len(data) < 2:
        flash('Nenhuma atividade encontrada com os filtros selecionados. Verifique os status, período ou condomínio escolhidos.', 'warning')
        return redirect(url_for('main.archive'))
    
    try:
        print(f"=== DEBUG: Criando tabela com {len(data)} linhas ===")
        print(f"=== DEBUG: Dados da tabela: {data} ===")
        table = Table(data, colWidths=[3.5*cm, 3.5*cm, 8*cm, 3*cm, 3*cm])
        print(f"=== DEBUG: Tabela criada com sucesso ===")
        
        # Criar lista de estilos da tabela
        table_style = [
            # Cabeçalho da tabela
            ('BACKGROUND', (0,0), (-1,0), empresa_blue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TOPPADDING', (0,0), (-1,0), 6),
            
            # Linhas alternadas para melhor legibilidade (apenas se houver mais de 1 linha de dados)
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ]
        
        # Aplicar linhas alternadas apenas se houver mais de 1 linha de dados
        if len(data) > 2:  # Mais de 1 linha de dados (além do cabeçalho)
            table_style.extend([
                ('BACKGROUND', (0,2), (-1,2), empresa_gray),
                ('BACKGROUND', (0,4), (-1,4), empresa_gray),
                ('BACKGROUND', (0,6), (-1,6), empresa_gray),
                ('BACKGROUND', (0,8), (-1,8), empresa_gray),
                ('BACKGROUND', (0,10), (-1,10), empresa_gray),
            ])
        
        # Adicionar estilos de alinhamento e formatação
        table_style.extend([
            # Alinhamento e formatação
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            
            # Bordas profissionais
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('LINEBELOW', (0,0), (-1,0), 1, empresa_blue),
            
            # Espaçamento interno reduzido
            ('BOTTOMPADDING', (0,1), (-1,-1), 6),
            ('TOPPADDING', (0,1), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ])
        
        table.setStyle(TableStyle(table_style))
        print(f"=== DEBUG: Estilo da tabela aplicado com sucesso ===")
        elements.append(table)
        print(f"=== DEBUG: Tabela adicionada aos elementos ===")
        
        # Se houver observações, adicionar seção após a tabela
        print(f"=== DEBUG: Total de observações: {len(observacoes)} ===")
        if observacoes:
            print(f"=== DEBUG: Adicionando seção de observações ===")
            elements.append(Spacer(1, 20))
            
            # Título da seção de observações
            obs_title_style = ParagraphStyle('obs_title', parent=styles['Normal'], 
                                           alignment=TA_CENTER, fontSize=12, fontName='Helvetica-Bold',
                                           textColor=empresa_blue, spaceAfter=12)
            elements.append(Paragraph('OBSERVAÇÕES', obs_title_style))
            
            # Estilo para as observações
            obs_style = ParagraphStyle('obs', parent=styles['Normal'],
                                     fontSize=10, fontName='Helvetica',
                                     leftIndent=20, spaceAfter=6)
            
            for titulo, status_str, motivo in observacoes:
                obs_text = f'• <b>{titulo} - {status_str}:</b> {motivo}'
                elements.append(Paragraph(obs_text, obs_style))
        
        # Nome do arquivo PDF
        nome_pdf = f'RELATORIO-{unidecode(nome_condominio).replace(" ", "_").upper()}.pdf'
        # Definir título do documento PDF (aba do visualizador)
        doc.title = f'RELATÓRIO - {nome_condominio}'
        print(f"=== DEBUG: Iniciando construção do PDF ===")
        print(f"=== DEBUG: Número de elementos: {len(elements)} ===")
        doc.build(elements, onFirstPage=create_header, onLaterPages=create_header)
        print(f"=== DEBUG: PDF construído com sucesso ===")
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=nome_pdf, mimetype='application/pdf')
    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")
        flash('Erro ao gerar o PDF. Verifique se há dados válidos para os filtros selecionados.', 'error')
        return redirect(url_for('main.archive')) 