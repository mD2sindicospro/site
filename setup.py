import os
import subprocess
import sys
from pathlib import Path
from app import create_app, db
from app.models.user import User
from app import bcrypt
from setuptools import setup, find_packages

def setup_database():
    app = create_app()
    with app.app_context():
        # Remove o banco de dados existente
        db.drop_all()
        # Cria um novo banco de dados
        db.create_all()
        
        # Cria o usuário admin
        admin = User(
            username='admin',
            email='admin@admin.com',
            password='admin123',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        
        print('Banco de dados configurado com sucesso!')
        print('Usuário admin criado:')
        print('Email: admin@admin.com')
        print('Senha: admin123')

def setup_environment():
    """Configura o ambiente de desenvolvimento."""
    print("🚀 Iniciando configuração do ambiente...")
    
    # Cria diretório de logs se não existir
    Path("logs").mkdir(exist_ok=True)
    
    # Cria arquivo .env se não existir
    if not os.path.exists(".env"):
        with open(".env", "w", encoding='utf-8') as f:
            f.write("""FLASK_APP=run.py
FLASK_DEBUG=True
SECRET_KEY=chave-secreta-desenvolvimento
CSRF_SECRET_KEY=csrf-chave-secreta-desenvolvimento
FLASK_HOST=127.0.0.1
FLASK_PORT=5000

# Configuração do Neon (substitua com sua URL do Neon)
DATABASE_URL=postgresql://user:password@ep-something.region.aws.neon.tech/neondb?sslmode=require

# Configurações de Email (opcional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-de-app
""")
        print("✅ Arquivo .env criado com sucesso!")
        print("⚠️ Por favor, edite o arquivo .env e configure sua URL do Neon!")
    
    # Instala dependências
    print("📦 Instalando dependências...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    
    # Verifica se a URL do Neon está configurada
    if not os.getenv('DATABASE_URL'):
        print("⚠️ DATABASE_URL não configurada! Configure sua URL do Neon no arquivo .env")
        return
    
    # Inicializa o banco de dados
    print("🗃️ Inicializando banco de dados...")
    try:
        subprocess.run([sys.executable, "-m", "flask", "db", "upgrade"], check=True)
    except subprocess.CalledProcessError:
        print("⚠️ Erro ao inicializar banco de dados. Verifique sua URL do Neon.")
        return
    
    # Cria usuário admin
    print("👤 Criando usuário administrador...")
    try:
        subprocess.run([sys.executable, "create_admin.py"], check=True)
    except subprocess.CalledProcessError:
        print("⚠️ Erro ao criar usuário admin. Verifique se o banco de dados está configurado corretamente.")
    
    print("""
✨ Configuração concluída com sucesso!

Para iniciar o servidor, execute:
    flask run

Para mais informações, consulte o README.md
""")

setup(
    name='site-m2d',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask==2.3.3',
        'Flask-SQLAlchemy==3.1.1',
        'Flask-Login==0.6.3',
        'Flask-WTF==1.2.1',
        'Flask-Migrate==4.0.5',
        'Flask-Bcrypt==1.0.1',
        'python-slugify==8.0.1',
        'python-dotenv==1.0.0',
        'email-validator==2.1.0',
        'Werkzeug==2.3.7',
        'SQLAlchemy==2.0.23',
        'alembic==1.12.1',
        'greenlet==3.0.3',
        'pytest==7.4.3',
        'pytest-cov==4.1.0',
        'pytest-flask==1.3.0'
    ],
    python_requires='>=3.8',
)

if __name__ == "__main__":
    setup_environment() 