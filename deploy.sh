#!/bin/bash

# Script de deploy otimizado para o Render
# Autor: Web Dev Experiente
# Data: $(date)

echo "🚀 Iniciando deploy do site-m2d..."

# Verificar se estamos no branch correto
if [ "$(git branch --show-current)" != "main" ]; then
    echo "⚠️  Você não está no branch main. Mudando para main..."
    git checkout main
fi

# Atualizar dependências
echo "📦 Atualizando dependências..."
pip install -r requirements.txt

# Executar migrações
echo "🗄️  Executando migrações do banco..."
flask db upgrade

# Verificar sintaxe Python
echo "🔍 Verificando sintaxe Python..."
python -m py_compile app/__init__.py
python -m py_compile app/routes/main.py
python -m py_compile app/routes/auth.py
python -m py_compile app/routes/admin.py
python -m py_compile app/routes/activity.py
python -m py_compile app/routes/property.py

# Testes básicos
echo "🧪 Executando testes básicos..."
python -c "
from app import create_app
app = create_app('testing')
print('✅ Aplicação criada com sucesso')
"

# Verificar health check
echo "🏥 Testando health check..."
python -c "
from app import create_app
app = create_app('testing')
with app.test_client() as client:
    response = client.get('/health')
    print(f'Health check status: {response.status_code}')
    if response.status_code == 200:
        print('✅ Health check funcionando')
    else:
        print('❌ Health check falhou')
"

# Commit e push
echo "📝 Fazendo commit das mudanças..."
git add .
git commit -m "🔧 Otimização: Health check routes e configuração Render

- Adicionadas rotas de health check (/health, /health-db, /health-detailed)
- Otimizada configuração do Gunicorn (1 worker, timeout 30s)
- Adicionado logging estruturado e middleware de performance
- Implementados templates de erro (404, 500)
- Adicionado psutil para monitoramento de sistema
- Configurado cache headers para arquivos estáticos
- Corrigido healthCheckPath no render.yaml

Resolve: Erro 429 no Render devido a health check loop"

echo "🚀 Fazendo push para o repositório..."
git push origin main

echo "✅ Deploy concluído!"
echo "📊 Monitoramento:"
echo "   - Health check: https://seu-app.onrender.com/health"
echo "   - Health DB: https://seu-app.onrender.com/health-db"
echo "   - Health detalhado: https://seu-app.onrender.com/health-detailed"
echo ""
echo "🔍 Para verificar logs:"
echo "   - Render Dashboard > Logs"
echo "   - Verificar se não há mais loops de health check" 