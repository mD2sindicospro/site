#!/usr/bin/env python3
"""
Script de teste para verificar o login por email e senha
"""

from app import create_app
from app.extensions import db
from app.models.user import User

def test_login_system():
    """Testa o sistema de login"""
    app = create_app('development')
    
    with app.app_context():
        # Verifica se existe um usuário admin
        admin = User.query.filter_by(email='admin@m2d.com').first()
        
        if not admin:
            print("❌ Usuário admin não encontrado!")
            print("Execute: python reset_db.py")
            return False
        
        print("✅ Usuário admin encontrado!")
        print(f"Email: {admin.email}")
        print(f"Nome: {admin.name}")
        print(f"Role: {admin.role}")
        print(f"Ativo: {admin.is_active}")
        
        # Testa a verificação de senha
        if admin.check_password('admin123'):
            print("✅ Senha 'admin123' está correta!")
        else:
            print("❌ Senha 'admin123' está incorreta!")
            return False
        
        # Testa senha incorreta
        if not admin.check_password('senha_errada'):
            print("✅ Senha incorreta rejeitada corretamente!")
        else:
            print("❌ Senha incorreta foi aceita!")
            return False
        
        print("\n🎉 Sistema de login funcionando corretamente!")
        print("\nPara testar no navegador:")
        print("1. Execute: flask run")
        print("2. Acesse: http://localhost:5000")
        print("3. Faça login com:")
        print("   Email: admin@m2d.com")
        print("   Senha: admin123")
        
        return True

if __name__ == '__main__':
    test_login_system() 