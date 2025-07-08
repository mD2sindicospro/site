#!/usr/bin/env python3
"""
Script para forçar redeploy e verificar health check
"""

import os
import sys
import subprocess

def check_health_endpoint():
    """Testa o health check localmente"""
    try:
        import requests
        response = requests.get('http://localhost:5000/health', timeout=5)
        print(f"✅ Health check local: {response.status_code}")
        print(f"Response: {response.text}")
        return True
    except Exception as e:
        print(f"❌ Health check local falhou: {e}")
        return False

def force_redeploy():
    """Força um redeploy no Render"""
    
    # Fazer commit de uma mudança pequena
    with open('force_redeploy.txt', 'w') as f:
        f.write(f"Redeploy forçado em {os.popen('date').read().strip()}")
    
    # Git commands
    commands = [
        "git add .",
        "git commit -m 'Force redeploy: Fix health check loop'",
        "git push origin main"
    ]
    
    for cmd in commands:
        print(f"Executando: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Erro: {result.stderr}")
            return False
        else:
            print(f"✅ Sucesso: {result.stdout}")
    
    return True

def create_test_script():
    """Cria script para testar health check"""
    
    test_script = '''#!/bin/bash

echo "🧪 Testando health check..."

# Teste local
echo "1. Teste local:"
python -c "
from app import create_app
app = create_app('testing')
with app.test_client() as client:
    response = client.get('/health')
    print(f'Status: {response.status_code}')
    print(f'Response: {response.data.decode()}')
"

# Teste remoto (se disponível)
echo "2. Teste remoto:"
curl -s https://md2-hjff.onrender.com/health || echo "Aplicação ainda não está disponível"

echo "✅ Testes concluídos"
'''
    
    with open('test_health.sh', 'w') as f:
        f.write(test_script)
    
    print("✅ Script test_health.sh criado")

def main():
    print("🔧 Forçando redeploy para corrigir health check loop...")
    
    # Criar script de teste
    create_test_script()
    
    # Forçar redeploy
    if force_redeploy():
        print("\n✅ Redeploy forçado com sucesso!")
        print("\n📋 Próximos passos:")
        print("1. Aguarde 2-5 minutos para o deploy")
        print("2. Execute: bash test_health.sh")
        print("3. Verifique logs no Render Dashboard")
        print("4. Teste login na aplicação")
        
        print("\n🔍 Para verificar se funcionou:")
        print("- Health check deve retornar 200 OK")
        print("- Logs não devem mostrar loops de /auth/login")
        print("- Login deve funcionar normalmente")
    else:
        print("❌ Erro ao forçar redeploy")
        sys.exit(1)

if __name__ == '__main__':
    main() 