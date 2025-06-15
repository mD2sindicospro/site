from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

# Inicialização das extensões
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()

def init_extensions(app):
    """Inicializa todas as extensões do Flask."""
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Configuração do login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'

    # Carrega o usuário para o Flask-Login
    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Importa os modelos na ordem correta de dependência
    with app.app_context():
        # Primeiro, importa o modelo base (User)
        from app.models.user import User
        
        # Depois, importa os modelos que dependem do User
        from app.models.message import Message
        from app.models.activity import Activity
        # from app.models.address import Address

        # Garante que o app está registrado com o SQLAlchemy
        if app not in db._app_engines:
            db._app_engines[app] = {}

        # Cria as tabelas se não existirem
        db.create_all() 