from flask import Flask, current_app
from flask import has_request_context
from app.forms.atividade import NovaAtividadeForm
from config import config
from app.extensions import init_extensions

def create_app(config_name='default'):
    app = Flask(__name__, static_folder='static')
    
    # Carrega a configuração
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Inicializa todas as extensões e cria as tabelas
    init_extensions(app)

    # Registra os blueprints
    from app.routes.auth import auth
    from app.routes.main import main
    from app.routes.admin import admin
    from app.routes.condominio import condominio
    from app.routes.atividade import atividade
    
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(main)
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(condominio, url_prefix='/condominio')
    app.register_blueprint(atividade, url_prefix='/atividade')

    @app.context_processor
    def inject_nova_atividade_form():
        if not has_request_context():
            return {'nova_atividade_form': NovaAtividadeForm()}
        try:
            from app.models.condominio import Condominio
            from app.models.user import User
            form = NovaAtividadeForm()
            if current_app and current_app.app_context():
                condominios = Condominio.query.filter_by(is_active=True).all()
                form.condominio.choices = [(c.id, c.nome) for c in condominios]
                users = User.query.filter_by(is_active=True).all()
                form.responsavel.choices = [(u.id, u.name) for u in users]
            return {'nova_atividade_form': form}
        except Exception as e:
            app.logger.error(f"Erro ao injetar formulário de atividade: {str(e)}")
            return {'nova_atividade_form': NovaAtividadeForm()}

    return app 