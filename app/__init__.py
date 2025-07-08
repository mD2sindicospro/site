from flask import Flask, current_app, request, g
from flask import has_request_context
from app.forms.activity import NewActivityForm
from config import config
from app.extensions import init_extensions
import time
import logging
from datetime import datetime
from flask import render_template
from app.extensions import db

def create_app(config_name='default'):
    app = Flask(__name__, static_folder='static')
    
    # Carrega a configuração
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Configurar logging estruturado
    if not app.debug:
        logging.basicConfig(level=logging.INFO)
        app.logger.setLevel(logging.INFO)

    # Middleware para logging de performance
    @app.before_request
    def before_request():
        g.start_time = time.time()
        g.request_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{id(request)}"

    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            app.logger.info(
                f"Request: {request.method} {request.path} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration:.3f}s - "
                f"IP: {request.remote_addr}"
            )
        return response

    # Middleware para otimização de cache
    @app.after_request
    def add_cache_headers(response):
        # Não cachear páginas que requerem autenticação
        if request.endpoint and 'auth' in request.endpoint:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        # Cachear arquivos estáticos por 1 ano
        elif request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'public, max-age=31536000'
        return response

    # Inicializa todas as extensões e cria as tabelas
    init_extensions(app)

    # Registra os blueprints
    from app.routes.auth import auth
    from app.routes.main import main
    from app.routes.admin import admin
    from app.routes.activity import activity
    from app.routes.property import property_bp
    
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(main)
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(activity, url_prefix='/activity')
    app.register_blueprint(property_bp)

    @app.context_processor
    def inject_new_activity_form():
        if not has_request_context():
            return {'new_activity_form': NewActivityForm()}
        try:
            from app.models.property import Property
            from app.models.user import User
            if current_app and current_app.app_context():
                properties = Property.query.filter_by(is_active=True).all()
                form = NewActivityForm()
                form.property.choices = [(p.id, p.name) for p in properties]
                users = User.query.filter_by(is_active=True).all()
                form.responsible.choices = [(u.id, u.name) for u in users]
            return {'new_activity_form': form}
        except Exception as e:
            app.logger.error(f"Erro ao injetar formulário de atividade: {str(e)}")
            return {'new_activity_form': NewActivityForm()}

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f"404 error: {request.url}")
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 error: {error}")
        try:
            # Tentar fazer rollback apenas se houver sessão ativa
            if hasattr(db, 'session') and db.session.is_active:
                db.session.rollback()
        except Exception as rollback_error:
            app.logger.error(f"Erro ao fazer rollback: {rollback_error}")
        
        return render_template('errors/500.html'), 500

    return app 