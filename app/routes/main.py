from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, send_file, current_app
from flask_login import login_required, current_user
from app.forms.atividade import NovaAtividadeForm
from app.models.condominio import Condominio
from app.models.user import User
from app.models.atividade import Atividade
from datetime import datetime, timedelta
from app.extensions import db
from app.models.mensagem import Mensagem
import pandas as pd
from io import BytesIO
from fpdf import FPDF

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

def serialize_atividade(a):
    return {
        'condominio': {'nome': a.condominio.nome if a.condominio else '—'},
        'data_lancamento': a.data_lancamento.strftime('%d/%m/%Y') if a.data_lancamento else '—',
        'atividade': a.atividade,
        'responsavel': {'username': a.responsavel.username if a.responsavel else '—'},
        'data_entrega': a.data_entrega.strftime('%d/%m/%Y') if a.data_entrega else '—',
        'status': a.status
    }

@main.route('/')
@login_required
def home():
    # Obter página atual da query string
    pagina_atual = request.args.get('pagina', 1, type=int)
    por_pagina = 20

    # Obter atividades baseado no papel do usuário
    if current_user.role == 'admin':
        query = Atividade.query
    elif current_user.role == 'supervisor':
        query = Atividade.query.join(Condominio).filter(Condominio.supervisor_id == current_user.id)
    else:
        query = Atividade.query.filter_by(responsavel_id=current_user.id)

    # Calcular total de páginas
    total_atividades = query.count()
    total_paginas = (total_atividades + por_pagina - 1) // por_pagina

    # Obter atividades da página atual
    atividades = query.order_by(Atividade.data_lancamento.desc())\
        .offset((pagina_atual - 1) * por_pagina)\
        .limit(por_pagina)\
        .all()

    # Criar formulário para nova atividade
    form = NovaAtividadeForm()
    form.condominio.choices = [(c.id, c.nome) for c in Condominio.query.filter_by(is_active=True).all()]
    form.responsavel.choices = [(u.id, u.username) for u in User.query.filter_by(is_active=True).all()]

    # Adiciona mensagem de boas-vindas
    flash(f'Bem-vindo, {current_user.username}!', 'success')
    return render_template('main/home.html',
                         atividades=atividades,
                         total_paginas=total_paginas,
                         pagina_atual=pagina_atual,
                         form=form)

@main.route('/home', methods=['GET', 'POST'])
@login_required
def home_post():
    current_app.logger.info(f'Usuário {current_user.username} acessou a página inicial')
    form = NovaAtividadeForm()
    condominios = Condominio.query.filter_by(is_active=True).all()
    form.condominio.choices = [(c.id, c.nome) for c in condominios]
    users = User.query.filter_by(is_active=True).all()
    form.responsavel.choices = [(u.id, u.username) for u in users]

    if request.method == 'POST':
        current_app.logger.info(f'Usuário {current_user.username} tentou criar uma nova atividade')
        # Converte data_entrega se vier como dd/mm/aaaa
        data_entrega_str = request.form.get('data_entrega')
        data_entrega = None
        if data_entrega_str:
            try:
                if '-' in data_entrega_str:
                    data_entrega = datetime.strptime(data_entrega_str, '%Y-%m-%d').date()
                else:
                    data_entrega = datetime.strptime(data_entrega_str, '%d/%m/%Y').date()
            except Exception as e:
                current_app.logger.error(f'Erro ao converter data: {str(e)}')
                flash('Data da entrega inválida. Use o formato dd/mm/aaaa.', 'danger')
                return redirect(url_for('main.home'))
        # Preenche o form manualmente para validação
        form.data_entrega.data = data_entrega
        form.data_entrega.raw_data = [data_entrega_str] if data_entrega_str else []

        if form.validate_on_submit():
            try:
                atividade = Atividade(
                    condominio_id=form.condominio.data,
                    responsavel_id=form.responsavel.data,
                    criado_por_id=current_user.id,
                    atividade=form.atividade.data,
                    descricao=form.descricao.data,
                    data_entrega=form.data_entrega.data,
                    resolvida=False,
                    status='pendente'
                )
                db.session.add(atividade)
                # Enviar mensagem informativa ao responsável
                msg = Mensagem(
                    usuario_destino_id=form.responsavel.data,
                    usuario_remetente_id=current_user.id,
                    assunto='Nova atividade atribuída',
                    corpo=f'{current_user.username} criou uma nova atividade para você: {form.atividade.data}',
                    lida=False
                )
                db.session.add(msg)
                db.session.commit()
                current_app.logger.info(f'Atividade criada com sucesso por {current_user.username}')
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

    # Paginação das atividades
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 20
    atividades_query = Atividade.query.order_by(Atividade.data_lancamento.desc())
    total_atividades = atividades_query.count()
    total_paginas = (total_atividades + por_pagina - 1) // por_pagina
    atividades = atividades_query.offset((pagina - 1) * por_pagina).limit(por_pagina).all()

    # Adiciona data_conclusao e status_color para cada atividade
    for a in atividades:
        a.data_conclusao = getattr(a, 'data_conclusao', None)
        if a.resolvida and not a.data_conclusao:
            a.data_conclusao = a.data_entrega
        # STATUS AUTOMÁTICO
        hoje = datetime.now().date()
        if hasattr(a, 'status') and a.status == 'finalizada':
            a.status_color = 'primary'
        elif hasattr(a, 'status') and a.status == 'realizada':
            a.status_color = 'success'
        elif hasattr(a, 'status') and a.status == 'em andamento':
            a.status_color = 'warning'
        elif hasattr(a, 'status') and a.status == 'ultimo dia':
            a.status_color = 'info'
        elif hasattr(a, 'status') and a.status == 'atrasada':
            a.status_color = 'danger'
        elif hasattr(a, 'status') and a.status == 'não realizada':
            a.status_color = 'secondary'
        elif hasattr(a, 'status') and a.status == 'correção':
            a.status_color = 'warning'
        else:
            # Cálculo automático do status
            if a.status == 'pendente':
                if a.data_entrega:
                    if hoje > a.data_entrega:
                        dias_atraso = (hoje - a.data_entrega).days
                        if dias_atraso >= 7:
                            a.status = 'não realizada'
                            a.status_color = 'secondary'
                        else:
                            a.status = 'atrasada'
                            a.status_color = 'danger'
                    elif hoje == a.data_entrega:
                        a.status = 'ultimo dia'
                        a.status_color = 'info'
                    else:
                        a.status = 'pendente'
                        a.status_color = 'secondary'
                else:
                    a.status = 'pendente'
                    a.status_color = 'secondary'
            elif a.status == 'em andamento':
                a.status_color = 'warning'
            elif a.status == 'realizada':
                a.status_color = 'success'
            elif a.status == 'finalizada':
                a.status_color = 'primary'
            else:
                a.status_color = 'secondary'

    # Cálculo dos percentuais para usuário normal ou supervisor
    percentual_pendentes = percentual_andamento = percentual_concluidas = percentual_atrasadas = percentual_nao_realizadas = 0
    total_condominios_supervisor = 0
    if current_user.role == 'normal':
        condominios_ativos = Condominio.query.filter_by(is_active=True).all()
        ids_ativos = [c.id for c in condominios_ativos]
        atividades_user = Atividade.query.filter(Atividade.responsavel_id == current_user.id, Atividade.condominio_id.in_(ids_ativos)).all()
        total_user = len(atividades_user)
        if total_user > 0:
            pendentes = sum(1 for a in atividades_user if a.status == 'pendente')
            andamento = sum(1 for a in atividades_user if a.status in ['em andamento', 'correção'])
            concluidas = sum(1 for a in atividades_user if a.status in ['realizada', 'finalizada'])
            atrasadas = sum(1 for a in atividades_user if a.status == 'atrasada')
            nao_realizadas = sum(1 for a in atividades_user if a.status == 'não realizada')
            percentual_pendentes = round((pendentes / total_user) * 100)
            percentual_andamento = round((andamento / total_user) * 100)
            percentual_concluidas = round((concluidas / total_user) * 100)
            percentual_atrasadas = round((atrasadas / total_user) * 100)
            percentual_nao_realizadas = round((nao_realizadas / total_user) * 100)
    elif current_user.role == 'supervisor':
        condominios_ativos = Condominio.query.filter_by(is_active=True).all()
        ids_ativos = [c.id for c in condominios_ativos]
        condominios_ids = [c.id for c in current_user.condominios if c.id in ids_ativos]
        total_condominios_supervisor = len(condominios_ids)
        atividades_supervisor = Atividade.query.filter(Atividade.condominio_id.in_(condominios_ids)).all()
        total_supervisor = len(atividades_supervisor)
        if total_supervisor > 0:
            pendentes = sum(1 for a in atividades_supervisor if a.status == 'pendente')
            andamento = sum(1 for a in atividades_supervisor if a.status in ['em andamento', 'correção'])
            concluidas = sum(1 for a in atividades_supervisor if a.status in ['realizada', 'finalizada'])
            atrasadas = sum(1 for a in atividades_supervisor if a.status == 'atrasada')
            nao_realizadas = sum(1 for a in atividades_supervisor if a.status == 'não realizada')
            percentual_pendentes = round((pendentes / total_supervisor) * 100)
            percentual_andamento = round((andamento / total_supervisor) * 100)
            percentual_concluidas = round((concluidas / total_supervisor) * 100)
            percentual_atrasadas = round((atrasadas / total_supervisor) * 100)
            percentual_nao_realizadas = round((nao_realizadas / total_supervisor) * 100)
    else:  # admin
        condominios_ativos = Condominio.query.filter_by(is_active=True).all()
        ids_ativos = [c.id for c in condominios_ativos]
        total_condominios_supervisor = len(ids_ativos)
        atividades_admin = Atividade.query.filter(Atividade.condominio_id.in_(ids_ativos)).all()
        total_admin = len(atividades_admin)
        if total_admin > 0:
            pendentes = sum(1 for a in atividades_admin if a.status == 'pendente')
            andamento = sum(1 for a in atividades_admin if a.status in ['em andamento', 'correção'])
            concluidas = sum(1 for a in atividades_admin if a.status in ['realizada', 'finalizada'])
            atrasadas = sum(1 for a in atividades_admin if a.status == 'atrasada')
            nao_realizadas = sum(1 for a in atividades_admin if a.status == 'não realizada')
            percentual_pendentes = round((pendentes / total_admin) * 100)
            percentual_andamento = round((andamento / total_admin) * 100)
            percentual_concluidas = round((concluidas / total_admin) * 100)
            percentual_atrasadas = round((atrasadas / total_admin) * 100)
            percentual_nao_realizadas = round((nao_realizadas / total_admin) * 100)

    # Atualiza status para 'atrasada' se vencida
    hoje = datetime.now().date()
    atividades_pendentes = Atividade.query.filter(
        Atividade.responsavel_id == current_user.id,
        Atividade.status == 'pendente',
        Atividade.data_entrega < hoje
    ).all()
    for at in atividades_pendentes:
        at.status = 'atrasada'
    if atividades_pendentes:
        db.session.commit()

    return render_template(
        'main/home.html',
        title='Início',
        form=form,
        atividades=atividades,
        total_paginas=total_paginas,
        pagina_atual=pagina,
        prazo_humano=prazo_humano,
        current_date=datetime.now().date(),
        percentual_pendentes=percentual_pendentes,
        percentual_andamento=percentual_andamento,
        percentual_concluidas=percentual_concluidas,
        percentual_atrasadas=percentual_atrasadas,
        percentual_nao_realizadas=percentual_nao_realizadas,
        total_condominios_supervisor=total_condominios_supervisor
    )

@main.route('/minhas-atividades')
@login_required
def minhas_atividades():
    # Atualiza status para 'atrasada' se vencida
    hoje = datetime.now().date()
    atividades_pendentes = Atividade.query.filter(
        Atividade.responsavel_id == current_user.id,
        Atividade.status == 'pendente',
        Atividade.data_entrega < hoje
    ).all()
    for at in atividades_pendentes:
        at.status = 'atrasada'
    if atividades_pendentes:
        db.session.commit()

    form = NovaAtividadeForm()
    condominios = Condominio.query.filter_by(is_active=True).all()
    form.condominio.choices = [(c.id, c.nome) for c in condominios]
    users = User.query.filter_by(is_active=True).all()
    form.responsavel.choices = [(u.id, u.username) for u in users]

    # Filtros
    filtro_condominio = request.args.get('condominio', type=int)
    filtro_status = request.args.get('status', type=str)

    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 20
    atividades_query = Atividade.query.filter(
        Atividade.responsavel_id == current_user.id,
        Atividade.status.notin_(['não realizada', 'finalizada'])
    )
    if filtro_condominio:
        atividades_query = atividades_query.filter(Atividade.condominio_id == filtro_condominio)
    if filtro_status:
        atividades_query = atividades_query.filter(Atividade.status == filtro_status)
    atividades_query = atividades_query.order_by(Atividade.data_lancamento.desc())
    total_atividades = atividades_query.count()
    total_paginas = (total_atividades + por_pagina - 1) // por_pagina
    atividades = atividades_query.offset((pagina - 1) * por_pagina).limit(por_pagina).all()

    for a in atividades:
        a.data_conclusao = getattr(a, 'data_conclusao', None)
        if a.resolvida and not a.data_conclusao:
            a.data_conclusao = a.data_entrega
        # STATUS AUTOMÁTICO (apenas cor)
        if hasattr(a, 'status') and a.status == 'finalizada':
            a.status_color = 'primary'
        elif hasattr(a, 'status') and a.status == 'realizada':
            a.status_color = 'success'
        elif hasattr(a, 'status') and a.status == 'em andamento':
            a.status_color = 'warning'
        elif hasattr(a, 'status') and a.status == 'ultimo dia':
            a.status_color = 'info'
        elif hasattr(a, 'status') and a.status == 'atrasada':
            a.status_color = 'danger'
        elif hasattr(a, 'status') and a.status == 'não realizada':
            a.status_color = 'secondary'
        elif hasattr(a, 'status') and a.status == 'correção':
            a.status_color = 'warning'
        else:
            a.status_color = 'secondary'

    return render_template(
        'main/minhas_atividades.html',
        title='Minhas Atividades',
        form=form,
        atividades=atividades,
        total_paginas=total_paginas,
        pagina_atual=pagina,
        prazo_humano=prazo_humano,
        current_date=datetime.now().date()
    )

@main.route('/atividade/<int:atividade_id>/aceitar', methods=['POST'])
@login_required
def aceitar_atividade(atividade_id):
    atividade = Atividade.query.get_or_404(atividade_id)
    if atividade.responsavel_id != current_user.id:
        abort(403)
    if atividade.status in ['pendente', 'correção']:
        atividade.status = 'em andamento'
        db.session.commit()
        flash('Atividade aceita com sucesso!', 'success')
    elif atividade.status == 'atrasada':
        flash('Atividade aceita, mas permanece como atrasada.', 'warning')
    return redirect(url_for('main.minhas_atividades'))

@main.route('/atividade/<int:atividade_id>/concluir', methods=['POST'])
@login_required
def concluir_atividade(atividade_id):
    atividade = Atividade.query.get_or_404(atividade_id)
    if atividade.responsavel_id != current_user.id:
        current_app.logger.warning(f'Usuário {current_user.username} tentou concluir atividade de outro usuário')
        abort(403)
    
    try:
        atividade.status = 'realizada'
        atividade.resolvida = True
        atividade.data_conclusao = datetime.now()
        db.session.commit()
        current_app.logger.info(f'Atividade {atividade_id} concluída por {current_user.username}')
        flash('Atividade concluída com sucesso!', 'success')
    except Exception as e:
        current_app.logger.error(f'Erro ao concluir atividade {atividade_id}: {str(e)}')
        db.session.rollback()
        flash('Erro ao concluir atividade. Tente novamente.', 'danger')
    
    return redirect(url_for('main.home'))

@main.route('/atividade/<int:atividade_id>/desistir', methods=['POST'])
@login_required
def desistir_atividade(atividade_id):
    atividade = Atividade.query.get_or_404(atividade_id)
    if atividade.responsavel_id != current_user.id:
        abort(403)
    if atividade.status in ['pendente', 'em andamento']:
        motivo = request.form.get('motivo_desistencia', '').strip()
        if not motivo:
            flash('É obrigatório informar o motivo do cancelamento.', 'danger')
            return redirect(url_for('main.minhas_atividades'))
        atividade.status = 'não realizada'
        atividade.resolvida = False
        atividade.motivo_desistencia = motivo
        db.session.commit()
        # Mensagem para o criador
        msg = Mensagem(
            usuario_destino_id=atividade.criado_por_id,
            usuario_remetente_id=current_user.id,
            assunto='Atividade cancelada',
            corpo=f'{current_user.username} cancelou uma atividade que você criou: {atividade.atividade}',
            lida=False
        )
        db.session.add(msg)
        db.session.commit()
        flash('Atividade cancelada com sucesso.', 'warning')
    return redirect(url_for('main.minhas_atividades'))

@main.route('/aprovacoes')
@login_required
def aprovacoes():
    if not hasattr(current_user, 'role') or current_user.role not in ['supervisor', 'admin']:
        abort(403)
    
    if current_user.role == 'supervisor':
        # Busca os condomínios onde o usuário é supervisor
        condominios_ids = [c.id for c in current_user.condominios]
        # Filtra atividades apenas dos condomínios onde é supervisor
        atividades = Atividade.query.filter(
            Atividade.status == 'realizada',
            Atividade.condominio_id.in_(condominios_ids)
        ).order_by(Atividade.data_lancamento.desc()).all()
    else:  # admin
        # Admin pode ver todas as atividades
        atividades = Atividade.query.filter_by(status='realizada').order_by(Atividade.data_lancamento.desc()).all()
    
    return render_template('main/aprovacoes.html', atividades=atividades)

@main.route('/aprovar-atividade/<int:atividade_id>', methods=['POST'])
@login_required
def aprovar_atividade(atividade_id):
    if not hasattr(current_user, 'role') or current_user.role not in ['supervisor', 'admin']:
        abort(403)
    atividade = Atividade.query.get_or_404(atividade_id)
    # Se for supervisor, não pode aprovar atividades criadas por supervisores
    if current_user.role == 'supervisor':
        if atividade.criado_por and atividade.criado_por.role == 'supervisor':
            flash('Apenas administradores podem aprovar atividades de supervisores.', 'danger')
            return redirect(url_for('main.aprovacoes'))
        condominios_ids = [c.id for c in current_user.condominios]
        if atividade.condominio_id not in condominios_ids:
            flash('Você não tem permissão para aprovar atividades deste condomínio.', 'danger')
            return redirect(url_for('main.aprovacoes'))
    if atividade.status == 'realizada':
        atividade.status = 'finalizada'
        atividade.resolvida = True
        atividade.aprovado_por_id = current_user.id
        db.session.commit()
        # Mensagem para o responsável
        msg = Mensagem(
            usuario_destino_id=atividade.responsavel_id,
            usuario_remetente_id=current_user.id,
            assunto='Atividade aprovada',
            corpo=f'{current_user.username} aprovou sua atividade: {atividade.atividade}',
            lida=False
        )
        db.session.add(msg)
        db.session.commit()
        flash('Atividade aprovada com sucesso!', 'success')
    else:
        flash('Apenas atividades realizadas podem ser aprovadas.', 'danger')
    return redirect(url_for('main.aprovacoes'))

@main.route('/recusar-atividade/<int:atividade_id>', methods=['POST'])
@login_required
def recusar_atividade(atividade_id):
    if not hasattr(current_user, 'role') or current_user.role not in ['supervisor', 'admin']:
        abort(403)
    atividade = Atividade.query.get_or_404(atividade_id)
    # Se for supervisor, não pode recusar atividades criadas por supervisores
    if current_user.role == 'supervisor':
        if atividade.criado_por and atividade.criado_por.role == 'supervisor':
            flash('Apenas administradores podem recusar atividades de supervisores.', 'danger')
            return redirect(url_for('main.aprovacoes'))
        condominios_ids = [c.id for c in current_user.condominios]
        if atividade.condominio_id not in condominios_ids:
            flash('Você não tem permissão para recusar atividades deste condomínio.', 'danger')
            return redirect(url_for('main.aprovacoes'))
    if atividade.status == 'realizada':
        atividade.status = 'não realizada'
        atividade.resolvida = False
        db.session.commit()
        flash('Atividade recusada com sucesso!', 'warning')
    else:
        flash('Apenas atividades realizadas podem ser recusadas.', 'danger')
    return redirect(url_for('main.aprovacoes'))

@main.route('/arquivo')
@login_required
def arquivo():
    form = NovaAtividadeForm()
    condominios = Condominio.query.filter_by(is_active=True).all()
    form.condominio.choices = [(c.id, c.nome) for c in condominios]
    users = User.query.filter_by(is_active=True).all()
    form.responsavel.choices = [(u.id, u.username) for u in users]

    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 20
    filtro_condominio = request.args.get('condominio', type=int)
    filtro_status = request.args.get('status', type=str)
    filtro_supervisor = request.args.get('supervisor', type=int)
    data_lancamento_inicio = request.args.get('data_lancamento_inicio')
    data_lancamento_fim = request.args.get('data_lancamento_fim')

    if current_user.role == 'supervisor':
        condominios_ids = [c.id for c in current_user.condominios]
        atividades_query = Atividade.query.filter(
            Atividade.condominio_id.in_(condominios_ids),
            Atividade.status.in_(['finalizada', 'não realizada'])
        )
    elif current_user.role == 'admin':
        atividades_query = Atividade.query.filter(
            Atividade.status.in_(['finalizada', 'não realizada'])
        )
    else:
        atividades_query = Atividade.query.filter(
            Atividade.responsavel_id == current_user.id,
            Atividade.status.in_(['finalizada', 'não realizada'])
        )

    if filtro_condominio:
        atividades_query = atividades_query.filter(Atividade.condominio_id == filtro_condominio)
    if filtro_status:
        atividades_query = atividades_query.filter(Atividade.status == filtro_status)
    if filtro_supervisor:
        atividades_query = atividades_query.join(Atividade.condominio).filter(Condominio.supervisor_id == filtro_supervisor)
    if data_lancamento_inicio:
        try:
            data_inicio = datetime.strptime(data_lancamento_inicio, '%d/%m/%Y')
        except ValueError:
            data_inicio = datetime.strptime(data_lancamento_inicio, '%Y-%m-%d')
        atividades_query = atividades_query.filter(Atividade.data_lancamento >= data_inicio)
    if data_lancamento_fim:
        try:
            data_fim = datetime.strptime(data_lancamento_fim, '%d/%m/%Y') + timedelta(days=1)
        except ValueError:
            data_fim = datetime.strptime(data_lancamento_fim, '%Y-%m-%d') + timedelta(days=1)
        atividades_query = atividades_query.filter(Atividade.data_lancamento < data_fim)

    atividades_query = atividades_query.order_by(Atividade.data_lancamento.desc())
    total_atividades = atividades_query.count()
    total_paginas = (total_atividades + por_pagina - 1) // por_pagina
    atividades = atividades_query.offset((pagina - 1) * por_pagina).limit(por_pagina).all()

    for a in atividades:
        a.data_conclusao = getattr(a, 'data_conclusao', None)
        if a.resolvida and not a.data_conclusao:
            a.data_conclusao = a.data_entrega
        hoje = datetime.now().date()
        if hasattr(a, 'status') and a.status == 'finalizada':
            a.status_color = 'primary'
        elif hasattr(a, 'status') and a.status == 'realizada':
            a.status_color = 'success'
        elif hasattr(a, 'status') and a.status == 'em andamento':
            a.status_color = 'warning'
        elif hasattr(a, 'status') and a.status == 'ultimo dia':
            a.status_color = 'info'
        elif hasattr(a, 'status') and a.status == 'atrasada':
            a.status_color = 'danger'
        elif hasattr(a, 'status') and a.status == 'não realizada':
            a.status_color = 'secondary'
        elif hasattr(a, 'status') and a.status == 'correção':
            a.status_color = 'warning'
        else:
            a.status_color = 'secondary'

    return render_template(
        'main/arquivo.html',
        title='Arquivo de Atividades',
        form=form,
        atividades=atividades,
        total_paginas=total_paginas,
        pagina_atual=pagina,
        prazo_humano=prazo_humano,
        current_date=datetime.now().date()
    )

@main.route('/atualizacoes')
@login_required
def atualizacoes():
    mensagens = (Mensagem.query
        .filter_by(usuario_destino_id=current_user.id)
        .order_by(Mensagem.data_criacao.desc())
        .limit(30)
        .all())
    return render_template('main/atualizacoes.html', mensagens=mensagens, current_date=datetime.now().date())

@main.route('/atividade/<int:atividade_id>/solicitar-correcao', methods=['POST'])
@login_required
def solicitar_correcao_atividade(atividade_id):
    if not hasattr(current_user, 'role') or current_user.role not in ['supervisor', 'admin']:
        abort(403)
    atividade = Atividade.query.get_or_404(atividade_id)
    # Se for supervisor, não pode solicitar correção de atividades criadas por supervisores
    if current_user.role == 'supervisor':
        if atividade.criado_por and atividade.criado_por.role == 'supervisor':
            flash('Apenas administradores podem solicitar correção de atividades de supervisores.', 'danger')
            return redirect(url_for('main.aprovacoes'))
        condominios_ids = [c.id for c in current_user.condominios]
        if atividade.condominio_id not in condominios_ids:
            flash('Você não tem permissão para solicitar correção desta atividade.', 'danger')
            return redirect(url_for('main.aprovacoes'))
    if atividade.status == 'realizada':
        motivo = request.form.get('motivo_correcao', '').strip()
        if not motivo:
            flash('É obrigatório informar o motivo da correção.', 'danger')
            return redirect(url_for('main.aprovacoes'))
        atividade.status = 'correção'
        atividade.resolvida = False
        atividade.motivo_correcao = motivo
        db.session.commit()
        # Mensagem para o responsável
        msg = Mensagem(
            usuario_destino_id=atividade.responsavel_id,
            usuario_remetente_id=current_user.id,
            assunto='Correção solicitada na atividade',
            corpo=f'{current_user.username} solicitou correção na sua atividade: {atividade.atividade}. Motivo: {motivo}',
            lida=False
        )
        db.session.add(msg)
        db.session.commit()
        flash('Correção solicitada com sucesso!', 'warning')
    else:
        flash('Apenas atividades realizadas podem ter correção solicitada.', 'danger')
    return redirect(url_for('main.aprovacoes'))

@main.route('/atividades-supervisor')
@login_required
def atividades_supervisor():
    if not hasattr(current_user, 'role') or current_user.role != 'supervisor':
        abort(403)
    condominios_ids = [c.id for c in current_user.condominios]
    filtro_condominio = request.args.get('condominio', type=int)
    filtro_status = request.args.get('status', type=str)
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 20
    atividades_query = Atividade.query.filter(
        Atividade.condominio_id.in_(condominios_ids),
        Atividade.status.notin_(['não realizada', 'finalizada'])
    )
    if filtro_condominio:
        atividades_query = atividades_query.filter(Atividade.condominio_id == filtro_condominio)
    if filtro_status:
        atividades_query = atividades_query.filter(Atividade.status == filtro_status)
    atividades_query = atividades_query.order_by(Atividade.data_lancamento.desc())
    total_atividades = atividades_query.count()
    total_paginas = (total_atividades + por_pagina - 1) // por_pagina
    atividades = atividades_query.offset((pagina - 1) * por_pagina).limit(por_pagina).all()
    for a in atividades:
        a.data_conclusao = getattr(a, 'data_conclusao', None)
        if a.resolvida and not a.data_conclusao:
            a.data_conclusao = a.data_entrega
        if hasattr(a, 'status') and a.status == 'finalizada':
            a.status_color = 'primary'
        elif hasattr(a, 'status') and a.status == 'realizada':
            a.status_color = 'success'
        elif hasattr(a, 'status') and a.status == 'em andamento':
            a.status_color = 'warning'
        elif hasattr(a, 'status') and a.status == 'ultimo dia':
            a.status_color = 'info'
        elif hasattr(a, 'status') and a.status == 'atrasada':
            a.status_color = 'danger'
        elif hasattr(a, 'status') and a.status == 'não realizada':
            a.status_color = 'secondary'
        elif hasattr(a, 'status') and a.status == 'correção':
            a.status_color = 'warning'
        else:
            a.status_color = 'secondary'
    condominios = current_user.condominios
    return render_template(
        'main/atividades_supervisor.html',
        title='Atividades dos Meus Condomínios',
        atividades=atividades,
        condominios=condominios,
        total_paginas=total_paginas,
        pagina_atual=pagina,
        filtro_condominio=filtro_condominio,
        filtro_status=filtro_status,
        prazo_humano=prazo_humano,
        current_date=datetime.now().date()
    )

@main.route('/arquivo/exportar-excel')
@login_required
def exportar_excel():
    filtro_condominio = request.args.get('condominio', type=int)
    filtro_status = request.args.get('status', type=str)
    filtro_supervisor = request.args.get('supervisor', type=int)
    data_lancamento_inicio = request.args.get('data_lancamento_inicio')
    data_lancamento_fim = request.args.get('data_lancamento_fim')
    if current_user.role == 'supervisor':
        condominios_ids = [c.id for c in current_user.condominios]
        atividades_query = Atividade.query.filter(
            Atividade.condominio_id.in_(condominios_ids),
            Atividade.status.in_(['finalizada', 'não realizada'])
        )
    elif current_user.role == 'admin':
        atividades_query = Atividade.query.filter(
            Atividade.status.in_(['finalizada', 'não realizada'])
        )
    else:
        atividades_query = Atividade.query.filter(
            Atividade.responsavel_id == current_user.id,
            Atividade.status.in_(['finalizada', 'não realizada'])
        )

    if filtro_condominio:
        atividades_query = atividades_query.filter(Atividade.condominio_id == filtro_condominio)
    if filtro_status:
        atividades_query = atividades_query.filter(Atividade.status == filtro_status)
    if filtro_supervisor:
        atividades_query = atividades_query.join(Atividade.condominio).filter(Condominio.supervisor_id == filtro_supervisor)
    if data_lancamento_inicio:
        try:
            data_inicio = datetime.strptime(data_lancamento_inicio, '%d/%m/%Y')
        except ValueError:
            data_inicio = datetime.strptime(data_lancamento_inicio, '%Y-%m-%d')
        atividades_query = atividades_query.filter(Atividade.data_lancamento >= data_inicio)
    if data_lancamento_fim:
        try:
            data_fim = datetime.strptime(data_lancamento_fim, '%d/%m/%Y') + timedelta(days=1)
        except ValueError:
            data_fim = datetime.strptime(data_lancamento_fim, '%Y-%m-%d') + timedelta(days=1)
        atividades_query = atividades_query.filter(Atividade.data_lancamento < data_fim)
    atividades_query = atividades_query.order_by(Atividade.data_lancamento.desc())
    atividades = atividades_query.all()
    data = []
    for a in atividades:
        data.append({
            'Condomínio': a.condominio.nome if a.condominio else '',
            'Lançamento': a.data_lancamento.strftime('%d/%m/%Y') if a.data_lancamento else '',
            'Responsável': a.responsavel.username if a.responsavel else '',
            'Atividade': a.atividade,
            'Entregar em': a.data_entrega.strftime('%d/%m/%Y') if a.data_entrega else '',
            'Concluída em': a.data_conclusao.strftime('%d/%m/%Y') if hasattr(a, 'data_conclusao') and a.data_conclusao else '',
            'Status': a.status,
        })
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Atividades')
    output.seek(0)
    return send_file(output, download_name='atividades_arquivo.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@main.route('/relatorios')
@login_required
def relatorios():
    if not (current_user.is_supervisor() or current_user.is_admin()):
        abort(403)
    form = NovaAtividadeForm()
    condominios = Condominio.query.filter_by(is_active=True).all()
    form.condominio.choices = [(c.id, c.nome) for c in condominios]
    users = User.query.filter_by(is_active=True).all()
    form.responsavel.choices = [(u.id, u.username) for u in users]

    # Totais globais para admin
    total_condominios = Condominio.query.count() if current_user.is_admin() else None
    total_usuarios = User.query.filter_by(is_active=True).count() if current_user.is_admin() else None
    total_pendentes = total_andamento = total_atrasadas = total_concluidas = total_nao_realizadas = 0
    percentual_pendentes = percentual_andamento = percentual_atrasadas = percentual_concluidas = percentual_nao_realizadas = 0
    if current_user.is_admin():
        condominios_ativos = Condominio.query.filter_by(is_active=True).all()
        ids_ativos = [c.id for c in condominios_ativos]
        total_condominios_supervisor = len(ids_ativos)
        atividades_admin = Atividade.query.filter(Atividade.condominio_id.in_(ids_ativos)).all()
        total_admin = len(atividades_admin)
        if total_admin > 0:
            pendentes = sum(1 for a in atividades_admin if a.status == 'pendente')
            andamento = sum(1 for a in atividades_admin if a.status in ['em andamento', 'correção'])
            concluidas = sum(1 for a in atividades_admin if a.status in ['realizada', 'finalizada'])
            atrasadas = sum(1 for a in atividades_admin if a.status == 'atrasada')
            nao_realizadas = sum(1 for a in atividades_admin if a.status == 'não realizada')
            percentual_pendentes = round((pendentes / total_admin) * 100)
            percentual_andamento = round((andamento / total_admin) * 100)
            percentual_concluidas = round((concluidas / total_admin) * 100)
            percentual_atrasadas = round((atrasadas / total_admin) * 100)
            percentual_nao_realizadas = round((nao_realizadas / total_admin) * 100)

    # Obtém os filtros da query string
    filtro_condominio = request.args.get('condominio', type=int)
    filtro_status = request.args.get('status', type=str)
    filtro_supervisor = request.args.get('supervisor', type=int)
    data_lancamento_inicio = request.args.get('data_lancamento_inicio')
    data_lancamento_fim = request.args.get('data_lancamento_fim')

    # Para admin, busca todas as atividades dos condomínios ativos
    if current_user.is_admin():
        condominios_ativos = Condominio.query.filter_by(is_active=True).all()
        ids_ativos = [c.id for c in condominios_ativos]
        atividades_query = Atividade.query.filter(Atividade.condominio_id.in_(ids_ativos))
    else:
        atividades_query = Atividade.query.filter_by(criado_por_id=current_user.id)

    # Aplica os filtros
    if filtro_condominio:
        atividades_query = atividades_query.filter(Atividade.condominio_id == filtro_condominio)
    if filtro_status:
        atividades_query = atividades_query.filter(Atividade.status == filtro_status)
    if filtro_supervisor:
        atividades_query = atividades_query.join(Atividade.condominio).filter(Condominio.supervisor_id == filtro_supervisor)
    if data_lancamento_inicio:
        try:
            data_inicio = datetime.strptime(data_lancamento_inicio, '%d/%m/%Y')
        except ValueError:
            data_inicio = datetime.strptime(data_lancamento_inicio, '%Y-%m-%d')
        atividades_query = atividades_query.filter(Atividade.data_lancamento >= data_inicio)
    if data_lancamento_fim:
        try:
            data_fim = datetime.strptime(data_lancamento_fim, '%d/%m/%Y') + timedelta(days=1)
        except ValueError:
            data_fim = datetime.strptime(data_lancamento_fim, '%Y-%m-%d') + timedelta(days=1)
        atividades_query = atividades_query.filter(Atividade.data_lancamento < data_fim)

    # Busca as atividades filtradas
    atividades = atividades_query.all()

    if current_user.is_admin():
        # Responsáveis comuns
        responsaveis = User.query.filter_by(is_active=True, role='normal').all()
        responsaveis_dict = {u.id: {
            'usuario': u,
                'pendentes': 0,
                'em_andamento': 0,
                'atrasadas': 0,
                'concluidas': 0,
                'nao_realizadas': 0,
                'tarefas': []
        } for u in responsaveis}
        # Supervisores
        supervisores = User.query.filter_by(is_active=True, role='supervisor').all()
        supervisores_dict = {u.id: {
            'usuario': u,
            'pendentes': 0,
            'em_andamento': 0,
            'atrasadas': 0,
            'concluidas': 0,
            'nao_realizadas': 0,
            'tarefas': [],
            'aguardando_aprovacao': 0
        } for u in supervisores}
        # Preenche os dados
        for a in atividades:
            if a.responsavel_id in responsaveis_dict:
                if a.status == 'pendente':
                    responsaveis_dict[a.responsavel_id]['pendentes'] += 1
                elif a.status in ['em andamento', 'correção']:
                    responsaveis_dict[a.responsavel_id]['em_andamento'] += 1
                elif a.status == 'atrasada':
                    responsaveis_dict[a.responsavel_id]['atrasadas'] += 1
                elif a.status in ['realizada', 'finalizada']:
                    responsaveis_dict[a.responsavel_id]['concluidas'] += 1
                elif a.status == 'não realizada':
                    responsaveis_dict[a.responsavel_id]['nao_realizadas'] += 1
                responsaveis_dict[a.responsavel_id]['tarefas'].append(serialize_atividade(a))
            if a.criado_por_id in supervisores_dict:
                if a.status == 'pendente':
                    supervisores_dict[a.criado_por_id]['pendentes'] += 1
                elif a.status in ['em andamento', 'correção']:
                    supervisores_dict[a.criado_por_id]['em_andamento'] += 1
                elif a.status == 'atrasada':
                    supervisores_dict[a.criado_por_id]['atrasadas'] += 1
                elif a.status in ['realizada', 'finalizada']:
                    supervisores_dict[a.criado_por_id]['concluidas'] += 1
                elif a.status == 'não realizada':
                    supervisores_dict[a.criado_por_id]['nao_realizadas'] += 1
                if a.status == 'realizada':
                    supervisores_dict[a.criado_por_id]['aguardando_aprovacao'] += 1
                supervisores_dict[a.criado_por_id]['tarefas'].append(serialize_atividade(a))
        # Serialização para os gráficos
        responsaveis_graficos = {}
        for uid, u in responsaveis_dict.items():
            responsaveis_graficos[uid] = {
                'usuario': {'id': u['usuario'].id, 'username': u['usuario'].username},
                'pendentes': u['pendentes'],
                'em_andamento': u['em_andamento'],
                'atrasadas': u['atrasadas'],
                'concluidas': u['concluidas'],
                'nao_realizadas': u['nao_realizadas'],
                'tarefas': u['tarefas']
            }
        supervisores_graficos = {}
        for uid, u in supervisores_dict.items():
            supervisores_graficos[uid] = {
                'usuario': {'id': u['usuario'].id, 'username': u['usuario'].username},
                'pendentes': u['pendentes'],
                'em_andamento': u['em_andamento'],
                'atrasadas': u['atrasadas'],
                'concluidas': u['concluidas'],
                'nao_realizadas': u['nao_realizadas'],
                'tarefas': u['tarefas'],
                'aguardando_aprovacao': u['aguardando_aprovacao']
            }
        return render_template(
            'main/relatorios.html',
            responsaveis_graficos=responsaveis_graficos,
            supervisores_graficos=supervisores_graficos,
            form=form,
            total_condominios=total_condominios,
            total_usuarios=total_usuarios,
            total_pendentes=total_pendentes,
            total_andamento=total_andamento,
            total_atrasadas=total_atrasadas,
            total_concluidas=total_concluidas,
            total_nao_realizadas=total_nao_realizadas,
            percentual_pendentes=percentual_pendentes,
            percentual_andamento=percentual_andamento,
            percentual_atrasadas=percentual_atrasadas,
            percentual_concluidas=percentual_concluidas,
            percentual_nao_realizadas=percentual_nao_realizadas
        )
    else:
        # Supervisor mantém lógica atual
        usuarios = {u.id: {
            'usuario': u,
            'pendentes': 0,
            'em_andamento': 0,
            'atrasadas': 0,
            'concluidas': 0,
            'nao_realizadas': 0,
            'tarefas': []
        } for u in users}
        for a in atividades:
            if a.responsavel_id in usuarios:
                if a.status == 'pendente':
                    usuarios[a.responsavel_id]['pendentes'] += 1
                elif a.status in ['em andamento', 'correção']:
                    usuarios[a.responsavel_id]['em_andamento'] += 1
                elif a.status == 'atrasada':
                    usuarios[a.responsavel_id]['atrasadas'] += 1
                elif a.status in ['realizada', 'finalizada']:
                    usuarios[a.responsavel_id]['concluidas'] += 1
                elif a.status == 'não realizada':
                    usuarios[a.responsavel_id]['nao_realizadas'] += 1
                usuarios[a.responsavel_id]['tarefas'].append(serialize_atividade(a))
    usuarios_graficos = {}
    for uid, u in usuarios.items():
        usuarios_graficos[uid] = {
            'usuario': {'id': u['usuario'].id, 'username': u['usuario'].username},
            'pendentes': u['pendentes'],
            'em_andamento': u['em_andamento'],
            'atrasadas': u['atrasadas'],
            'concluidas': u['concluidas'],
            'nao_realizadas': u['nao_realizadas']
        }
    return render_template(
        'main/relatorios.html',
        usuarios=usuarios,
        usuarios_graficos=usuarios_graficos,
        form=form,
        total_condominios=total_condominios,
        total_usuarios=total_usuarios,
        total_pendentes=total_pendentes,
        total_andamento=total_andamento,
        total_atrasadas=total_atrasadas,
        total_concluidas=total_concluidas,
        total_nao_realizadas=total_nao_realizadas,
        percentual_pendentes=percentual_pendentes,
        percentual_andamento=percentual_andamento,
        percentual_atrasadas=percentual_atrasadas,
        percentual_concluidas=percentual_concluidas,
        percentual_nao_realizadas=percentual_nao_realizadas
    ) 

@main.route('/atividades-admin')
@login_required
def atividades_admin():
    if not current_user.is_admin():
        abort(403)
    condominios = Condominio.query.filter_by(is_active=True).all()
    filtro_condominio = request.args.get('condominio', type=int)
    filtro_status = request.args.get('status', type=str)
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 20
    atividades_query = Atividade.query.filter(
        Atividade.condominio_id.in_([c.id for c in condominios]),
        Atividade.status.notin_(['não realizada', 'finalizada'])
    )
    if filtro_condominio:
        atividades_query = atividades_query.filter(Atividade.condominio_id == filtro_condominio)
    if filtro_status:
        atividades_query = atividades_query.filter(Atividade.status == filtro_status)
    atividades_query = atividades_query.order_by(Atividade.data_lancamento.desc())
    total_atividades = atividades_query.count()
    total_paginas = (total_atividades + por_pagina - 1) // por_pagina
    atividades = atividades_query.offset((pagina - 1) * por_pagina).limit(por_pagina).all()
    return render_template(
        'main/atividades_supervisor.html',
        title='Atividades de Todos os Condomínios',
        atividades=atividades,
        condominios=condominios,
        total_paginas=total_paginas,
        pagina_atual=pagina,
        filtro_condominio=filtro_condominio,
        filtro_status=filtro_status,
        prazo_humano=prazo_humano,
        current_date=datetime.now().date()
    ) 