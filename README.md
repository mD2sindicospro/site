# Sistema de Gestão de Atividades - M2D

Sistema completo de gestão de atividades desenvolvido em Flask para controle e acompanhamento de tarefas em condomínios e propriedades.

## 🚀 Funcionalidades Principais

### 👥 Gestão de Usuários
- **Autenticação segura** com Flask-Login e Flask-Bcrypt
- **Controle de acesso baseado em roles** (admin, supervisor, usuário normal)
- **Perfis de usuário** com informações detalhadas
- **Ativação/desativação** de usuários
- **Recuperação de senha** (preparado para implementação)

### 🏢 Gestão de Condomínios/Propriedades
- **Cadastro completo** de propriedades
- **Atribuição de supervisores** por propriedade
- **Ativação/desativação** de propriedades
- **Controle de apartamentos** por propriedade
- **Endereçamento** completo

### 📋 Gestão de Atividades
- **Criação de atividades** com descrição detalhada
- **Atribuição de responsáveis** por atividade
- **Definição de prazos** e datas de entrega
- **Controle de status** (pendente, em andamento, concluída, etc.)
- **Sistema de aprovação** para atividades concluídas
- **Notificações automáticas** entre usuários
- **Histórico completo** de mudanças

### 📊 Relatórios e Exportação
- **Exportação para Excel** com pandas e xlsxwriter
- **Geração de PDF** com reportlab e fpdf
- **Estatísticas detalhadas** por período e condomínio
- **Filtros avançados** por status, responsável, propriedade
- **Dashboard com métricas** em tempo real

### 💬 Sistema de Comunicação
- **Sistema de mensagens** interno
- **Notificações automáticas** para novas atividades
- **Histórico de comunicação** entre usuários
- **Mensagens de sistema** para atualizações importantes

## 🛠️ Tecnologias Utilizadas

### Backend
- **Flask 2.3.3** - Framework web principal
- **SQLAlchemy 2.0.23** - ORM para banco de dados
- **Flask-SQLAlchemy 3.1.1** - Integração Flask + SQLAlchemy
- **Flask-Login 0.6.3** - Sistema de autenticação
- **Flask-WTF 1.2.1** - Formulários e validação
- **Flask-Migrate 4.0.5** - Migrações de banco de dados
- **Flask-Bcrypt 1.0.1** - Criptografia de senhas

### Banco de Dados
- **PostgreSQL** - Banco de dados principal (via Neon)
- **SQLite** - Banco de dados para desenvolvimento
- **Alembic 1.12.1** - Migrações e versionamento
- **psycopg2-binary 2.9.9** - Driver PostgreSQL
- **pg8000 1.30.3** - Driver PostgreSQL alternativo

### Validação e Formatação
- **email-validator 2.1.0** - Validação de emails
- **python-slugify 8.0.1** - Formatação de URLs
- **python-dotenv 1.0.0** - Variáveis de ambiente
- **unidecode 1.3.7** - Normalização de texto

### Geração de Relatórios
- **pandas 2.2.2** - Manipulação de dados
- **xlsxwriter 3.1.9** - Criação de arquivos Excel
- **reportlab 4.0.7** - Geração de PDFs
- **fpdf 1.7.2** - Geração de PDFs alternativo

### Produção e Deploy
- **gunicorn 21.2.0** - Servidor WSGI para produção
- **whitenoise 6.6.0** - Servir arquivos estáticos
- **Werkzeug 2.3.7** - Utilitários WSGI

### Testes
- **pytest 7.4.3** - Framework de testes
- **pytest-cov 4.1.0** - Cobertura de testes
- **pytest-flask 1.3.0** - Testes específicos para Flask

## 📋 Pré-requisitos

- **Python 3.8+** (recomendado 3.11+)
- **pip** (gerenciador de pacotes Python)
- **Git** (para controle de versão)
- **PostgreSQL** (para produção) ou **SQLite** (para desenvolvimento)

## 🚀 Instalação

### 1. Clone o repositório
```bash
git clone [URL_DO_REPOSITÓRIO]
cd site-m2d
```

### 2. Crie e ative o ambiente virtual
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto:
```env
# Configurações básicas
FLASK_APP=wsgi.py
FLASK_ENV=development
SECRET_KEY=sua_chave_secreta_aqui
CSRF_SECRET_KEY=sua_chave_csrf_aqui

# Banco de dados (desenvolvimento)
DATABASE_URL=sqlite:///dev.db

# Banco de dados (produção - Neon)
# DATABASE_URL=postgresql://user:password@ep-something.region.aws.neon.tech/neondb?sslmode=require

# Configurações de email (opcional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-de-app

# Logs
LOG_LEVEL=INFO
LOG_TO_STDOUT=false
```

### 5. Inicialize o banco de dados
```bash
# Criar as migrações
flask db init

# Aplicar as migrações
flask db upgrade
```

### 6. Crie um usuário administrador
```bash
python reset_db.py
```

## 🏃‍♂️ Executando o Projeto

### Desenvolvimento
```bash
# Ative o ambiente virtual (se ainda não estiver ativo)
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Execute o servidor de desenvolvimento
flask run
```

O servidor estará disponível em `http://localhost:5000`

### Produção
```bash
# Usando gunicorn
gunicorn "wsgi:app" --bind 0.0.0.0:8000 --workers 4

# Ou usando o comando padrão
python wsgi.py
```

## 📁 Estrutura do Projeto

```
site-m2d/
├── app/                          # Aplicação principal
│   ├── __init__.py              # Inicialização da aplicação
│   ├── extensions.py             # Configuração de extensões
│   ├── models/                   # Modelos do banco de dados
│   │   ├── __init__.py
│   │   ├── user.py              # Modelo de usuário
│   │   ├── property.py          # Modelo de propriedade
│   │   ├── activity.py          # Modelo de atividade
│   │   └── message.py           # Modelo de mensagem
│   ├── routes/                   # Rotas da aplicação
│   │   ├── auth.py              # Autenticação
│   │   ├── main.py              # Páginas principais
│   │   ├── admin.py             # Área administrativa
│   │   ├── activity.py          # Gestão de atividades
│   │   └── property.py          # Gestão de propriedades
│   ├── forms/                    # Formulários
│   │   ├── auth.py              # Formulários de autenticação
│   │   └── activity.py          # Formulários de atividade
│   ├── templates/                # Templates HTML
│   │   ├── base.html            # Template base
│   │   ├── auth/                # Templates de autenticação
│   │   ├── main/                # Templates principais
│   │   ├── admin/               # Templates administrativos
│   │   └── activity/            # Templates de atividades
│   ├── static/                   # Arquivos estáticos
│   │   ├── css/                 # Estilos CSS
│   │   ├── js/                  # Scripts JavaScript
│   │   ├── images/              # Imagens
│   │   └── uploads/             # Uploads de arquivos
│   └── utils/                    # Utilitários
│       └── translations.py      # Traduções e formatação
├── migrations/                   # Migrações do banco de dados
├── tests/                        # Testes automatizados
│   ├── conftest.py              # Configuração de testes
│   ├── unit/                    # Testes unitários
│   └── integration/             # Testes de integração
├── scripts/                      # Scripts utilitários
├── logs/                         # Logs da aplicação
├── config.py                     # Configurações da aplicação
├── wsgi.py                       # Entry point para produção
├── requirements.txt              # Dependências do projeto
├── pytest.ini                   # Configuração do pytest
├── alembic.ini                  # Configuração do Alembic
├── render.yaml                   # Configuração de deploy (Render)
└── Procfile                      # Configuração de deploy (Heroku)
```

## 🧪 Testes

### Executar todos os testes
```bash
python -m pytest
```

### Executar testes com cobertura
```bash
python -m pytest --cov=app --cov-report=html
```

### Executar testes específicos
```bash
# Testes unitários
python -m pytest tests/unit/

# Testes de integração
python -m pytest tests/integration/

# Testes específicos
python -m pytest tests/test_models/test_user.py
```

## 📊 Funcionalidades Detalhadas

### Sistema de Status de Atividades
- **Pendente** - Atividade criada, aguardando início
- **Em Andamento** - Atividade sendo executada
- **Em Verificação** - Atividade concluída, aguardando aprovação
- **Correção** - Atividade precisa de ajustes
- **Não Realizada** - Atividade não foi executada
- **Atrasada** - Atividade vencida
- **Realizada** - Atividade aprovada e finalizada
- **Cancelada** - Atividade cancelada

### Controle de Acesso
- **Admin**: Acesso total ao sistema
- **Supervisor**: Gerencia propriedades e atividades
- **Usuário Normal**: Executa atividades atribuídas

### Sistema de Notificações
- Notificações automáticas para novas atividades
- Mensagens entre usuários
- Alertas de prazo vencido
- Confirmações de aprovação/rejeição

## 🔧 Scripts Utilitários

### Verificar conexão com banco de dados
```bash
python check_db.py
```

### Resetar banco de dados (desenvolvimento)
```bash
python reset_db.py
```

### Resetar banco de dados (produção)
```bash
python reset_prod_db.py
```

### Atualizar status de atividades
```bash
python scripts/update_status_realizada_to_done.py
```

## 📝 Logs

O sistema mantém logs detalhados em `logs/app.log` com:
- Data e hora
- Nível do log (INFO, WARNING, ERROR)
- Mensagem detalhada
- Arquivo e linha onde o log foi gerado

## 🚀 Deploy

### Render (Recomendado)
O projeto está configurado para deploy automático no Render:
- Configuração em `render.yaml`
- Deploy automático a cada push
- Banco PostgreSQL gerenciado
- SSL automático

### Heroku
```bash
# Instalar Heroku CLI
# Configurar variáveis de ambiente
heroku config:set SECRET_KEY=sua_chave
heroku config:set DATABASE_URL=sua_url_do_banco

# Deploy
git push heroku main
```

### VPS/Docker
```bash
# Construir imagem
docker build -t site-m2d .

# Executar container
docker run -p 8000:8000 site-m2d
```

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📞 Suporte

Para reportar problemas ou solicitar novas funcionalidades:
- Abra uma issue no repositório
- Descreva detalhadamente o problema ou solicitação
- Inclua logs de erro quando relevante

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🆕 Changelog

### v1.0.0
- Sistema completo de gestão de atividades
- Controle de usuários e propriedades
- Sistema de notificações
- Relatórios em Excel e PDF
- Deploy automatizado no Render

---

**Desenvolvido com ❤️ para facilitar a gestão de atividades em condomínios e propriedades.** 