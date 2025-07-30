from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.property import Property
from app.models.user import User
from app.extensions import db
from datetime import datetime
from app.utils.image_handler import ImageHandler

property_bp = Blueprint('property', __name__, url_prefix='/condominios')

@property_bp.route('/', methods=['GET', 'POST'])
@login_required
def list():
    # Carregar supervisores para o select
    supervisores = User.query.filter_by(role='supervisor', is_active=True).all()
    if request.method == 'POST' and current_user.is_admin:
        # Ativar/Inativar condomínio
        toggle_id = request.form.get('toggle_active_property_id')
        if toggle_id:
            property_obj = Property.query.get(toggle_id)
            if property_obj:
                property_obj.is_active = not property_obj.is_active
                db.session.commit()
                flash(f'Condomínio {"ativado" if property_obj.is_active else "inativado"} com sucesso!', 'success')
            else:
                flash('Condomínio não encontrado.', 'danger')
            return redirect(url_for('property.list'))
        # Edição/Criação
        edit_property_id = request.form.get('edit_property_id')
        nome = request.form.get('nome')
        data_entrada = request.form.get('data_entrada')
        endereco = request.form.get('endereco')
        estado = request.form.get('estado')
        supervisor_id = request.form.get('supervisor_id') or request.form.get('edit_supervisor_id') or None
        is_active = (request.form.get('is_active') == '1') if request.form.get('is_active') is not None else (request.form.get('edit_is_active') == '1')
        numero_apartamentos = request.form.get('numero_apartamentos') or request.form.get('edit_numero_apartamentos')
        administrador_nome = request.form.get('administrador_nome') or request.form.get('edit_administrador_nome')
        administrador_telefone = request.form.get('administrador_telefone') or request.form.get('edit_administrador_telefone')
        administrador_email = request.form.get('administrador_email') or request.form.get('edit_administrador_email')
        
        # Processamento da logo
        logo_url = request.form.get('logo_url')
        # Converter data para formato datetime
        entry_date = None
        if data_entrada:
            try:
                entry_date = datetime.strptime(data_entrada, '%d/%m/%Y')
            except ValueError:
                entry_date = None
        if edit_property_id:
            # Edição
            property_obj = Property.query.get(edit_property_id)
            if property_obj:
                # Atualiza a URL da logo
                property_obj.logo_url = logo_url
                property_obj.name = nome
                property_obj.address = endereco
                property_obj.number_of_apartments = numero_apartamentos
                property_obj.supervisor_id = supervisor_id if supervisor_id else None
                property_obj.is_active = is_active
                property_obj.entry_date = entry_date
                property_obj.state = estado
                property_obj.administrator_name = administrador_nome
                property_obj.administrator_phone = administrador_telefone
                property_obj.administrator_email = administrador_email
                db.session.commit()
                flash('Condomínio atualizado com sucesso!', 'success')
            else:
                flash('Condomínio não encontrado para edição.', 'danger')
        else:
            # Criação
            property_obj = Property(
                name=nome,
                address=endereco,
                number_of_apartments=numero_apartamentos,
                supervisor_id=supervisor_id if supervisor_id else None,
                is_active=is_active,
                entry_date=entry_date,
                state=estado,
                administrator_name=administrador_nome,
                administrator_phone=administrador_telefone,
                administrator_email=administrador_email,
                logo_url=logo_url
            )
            db.session.add(property_obj)
            db.session.commit()
            
            flash('Condomínio cadastrado com sucesso!', 'success')
        return redirect(url_for('property.list'))
    # Paginação
    page = request.args.get('page', 1, type=int)
    per_page = 10
    properties_query = Property.query.order_by(Property.number_of_apartments.desc())
    total_properties = properties_query.count()
    total_pages = (total_properties + per_page - 1) // per_page
    properties = properties_query.offset((page - 1) * per_page).limit(per_page).all()
    
    return render_template('condominio/listar.html', 
                          properties=properties, 
                          supervisores=supervisores,
                          total_pages=total_pages,
                          current_page=page) 