from flask import Flask, current_app
from flask import has_request_context
from app.forms.activity import NewActivityForm
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
            form = NewActivityForm()
            if current_app and current_app.app_context():
                properties = Property.query.filter_by(is_active=True).all()
                form.property.choices = [(p.id, p.name) for p in properties]
                users = User.query.filter_by(is_active=True).all()
                form.responsible.choices = [(u.id, u.name) for u in users]
            return {'new_activity_form': form}
        except Exception as e:
            app.logger.error(f"Erro ao injetar formulário de atividade: {str(e)}")
            return {'new_activity_form': NewActivityForm()}

    return app 