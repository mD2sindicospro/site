from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.forms.atividade import NovaAtividadeForm
from app.models.atividade import Atividade
from app.models.condominio import Condominio
from app.models.user import User
from app.extensions import db
from datetime import datetime

activity = Blueprint('activity', __name__)

@activity.route('/activities/new', methods=['GET', 'POST'])
@login_required
def new_activity():
    form = NovaAtividadeForm()
    # Popula o select de condomínios
    condominios = Condominio.query.filter_by(is_active=True).all()
    form.condominio.choices = [(c.id, c.nome) for c in condominios]
    # Popula o select de responsáveis (todos os usuários ativos)
    users = User.query.filter_by(is_active=True).all()
    form.responsavel.choices = [(u.id, u.username) for u in users]

    if form.validate_on_submit():
        atividade = Atividade(
            condominio_id=form.condominio.data,
            responsavel_id=form.responsavel.data,
            criado_por_id=current_user.id,
            descricao=form.descricao.data,
            data_entrega=form.data_entrega.data,
            resolvida=False,
            status='pendente'
        )
        db.session.add(atividade)
        db.session.commit()
        flash('Atividade criada com sucesso!', 'success')
        return redirect(url_for('main.home'))
    return render_template('activity/new.html', form=form)

@activity.route('/atividade/nova', methods=['POST'])
@login_required
def criar_atividade():
    form = NovaAtividadeForm()
    condominios = Condominio.query.filter_by(is_active=True).all()
    form.condominio.choices = [(c.id, c.nome) for c in condominios]
    users = User.query.filter_by(is_active=True).all()
    form.responsavel.choices = [(u.id, u.username) for u in users]

    if form.validate_on_submit():
        # Conversão da data_entrega (string para date)
        data_entrega_str = form.data_entrega.data
        data_entrega = None
        if data_entrega_str:
            try:
                if '-' in data_entrega_str:
                    data_entrega = datetime.strptime(data_entrega_str, '%Y-%m-%d').date()
                else:
                    data_entrega = datetime.strptime(data_entrega_str, '%d/%m/%Y').date()
            except Exception:
                flash('Data da entrega inválida. Use o formato dd/mm/aaaa.', 'danger')
                next_url = request.form.get('next') or request.referrer or url_for('main.home')
                return redirect(next_url)
        atividade = Atividade(
            condominio_id=form.condominio.data,
            responsavel_id=form.responsavel.data,
            criado_por_id=current_user.id,
            atividade=form.atividade.data,
            descricao=form.descricao.data,
            data_entrega=data_entrega,
            resolvida=False,
            status='pendente'
        )
        db.session.add(atividade)
        db.session.commit()
        flash('Atividade criada com sucesso!', 'success')
    else:
        flash('Erro ao criar atividade. Verifique os campos e tente novamente.', 'danger')

    next_url = request.form.get('next') or request.referrer or url_for('main.home')
    return redirect(next_url) 