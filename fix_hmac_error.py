#!/usr/bin/env python3
"""
Script de correção para erro HMAC e problemas de compatibilidade
"""

import os
import sys

def fix_main_py():
    """Corrige o arquivo main.py removendo psutil"""
    
    main_py_path = 'app/routes/main.py'
    
    # Ler o arquivo
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remover import psutil
    content = content.replace('import psutil', '# import psutil  # Temporarily disabled')
    
    # Substituir função health-detailed
    old_health_detailed = '''@main.route('/health-detailed')
def health_check_detailed():
    """
    Rota para health check detalhado com métricas do sistema.
    """
    try:
        # Informações básicas do sistema
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
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
            'system': {
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'cpu_percent': psutil.cpu_percent(interval=1)
            },
            'database': db_status,
            'environment': os.getenv('FLASK_ENV', 'development')
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500'''
    
    new_health_detailed = '''@main.route('/health-detailed')
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
        }), 500'''
    
    content = content.replace(old_health_detailed, new_health_detailed)
    
    # Salvar arquivo
    with open(main_py_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ main.py corrigido")

def fix_init_py():
    """Corrige o arquivo __init__.py"""
    
    init_py_path = 'app/__init__.py'
    
    # Ler o arquivo
    with open(init_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Substituir error handler 500
    old_error_handler = '''    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 error: {error}")
        db.session.rollback()
        return render_template('errors/500.html'), 500'''
    
    new_error_handler = '''    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 error: {error}")
        try:
            # Tentar fazer rollback apenas se houver sessão ativa
            if hasattr(db, 'session') and db.session.is_active:
                db.session.rollback()
        except Exception as rollback_error:
            app.logger.error(f"Erro ao fazer rollback: {rollback_error}")
        
        return render_template('errors/500.html'), 500'''
    
    content = content.replace(old_error_handler, new_error_handler)
    
    # Salvar arquivo
    with open(init_py_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ __init__.py corrigido")

def fix_requirements():
    """Atualiza requirements.txt com versões compatíveis"""
    
    req_path = 'requirements.txt'
    
    # Nova versão do requirements.txt
    new_content = '''# Flask e extensões principais
Flask==2.3.4
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1
Flask-Migrate==4.0.5
Flask-Bcrypt==1.0.1

# Banco de dados e ORM
SQLAlchemy==2.0.23
alembic==1.12.1
greenlet==3.0.3

# Drivers de banco de dados
psycopg2-binary==2.9.9
pg8000==1.30.3

# Validação e formatação
email-validator==2.1.0
python-slugify==8.0.1
python-dotenv==1.0.0

# Utilitários
Werkzeug==3.0.1
unidecode==1.3.7

# Geração de relatórios
pandas==2.2.2
fpdf==1.7.2
xlsxwriter==3.1.9
reportlab==4.0.7

# Servidor de produção
gunicorn==21.2.0
whitenoise==6.6.0

# Testes
pytest==7.4.3
pytest-cov==4.1.0
pytest-flask==1.3.0

# Desenvolvimento (opcional)
# python-dotenv==1.0.0  # Já incluído acima'''
    
    # Salvar arquivo
    with open(req_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ requirements.txt atualizado")

def create_fix_script():
    """Cria script de deploy rápido"""
    
    script_content = '''#!/bin/bash

echo "🔧 Aplicando correções para erro HMAC..."

# Atualizar dependências
pip install -r requirements.txt

# Executar migrações
flask db upgrade

# Teste básico
python -c "
from app import create_app
app = create_app('testing')
print('✅ Aplicação criada com sucesso')
"

# Commit e push
git add .
git commit -m "Fix: Resolve HMAC error and compatibility issues

- Updated Flask to 2.3.4
- Updated Werkzeug to 3.0.1 for Python 3.11 compatibility
- Removed psutil dependency
- Fixed health check detailed endpoint
- Improved error handler 500

Resolves: TypeError: Missing required argument 'digestmod'"
git push origin main

echo "✅ Correções aplicadas e deployado!"
'''
    
    with open('quick_fix.sh', 'w') as f:
        f.write(script_content)
    
    print("✅ Script quick_fix.sh criado")

if __name__ == '__main__':
    print("🔧 Aplicando correções para erro HMAC...")
    
    try:
        fix_main_py()
        fix_init_py()
        fix_requirements()
        create_fix_script()
        
        print("\n✅ Todas as correções aplicadas!")
        print(" Execute o script de deploy:")
        print("   bash quick_fix.sh")
        print("\n Ou faça manualmente:")
        print("   git add .")
        print("   git commit -m 'Fix: Resolve HMAC error'")
        print("   git push origin main")
        
    except Exception as e:
        print(f"❌ Erro ao aplicar correções: {e}")
        sys.exit(1) 