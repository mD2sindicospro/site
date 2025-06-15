# Activity Management System

A Flask-based activity management system for property management and task tracking.

## Features

### Activity Management
- Activity creation
- Activity status tracking
- Activity assignment
- Activity approval workflow
- Activity statistics

### Property Management
- Property registration
- Property details
- Property statistics

### User Management
- User registration
- Role-based access control
- User profile management

### Communication
- Message system
- Notifications
- Activity updates

## Technical Details

### Models
- Activity
- Property
- User
- Message

### Routes
- Activity routes
- Property routes
- User routes
- Message routes

### Templates
- Activity templates
- Property templates
- User templates
- Message templates

## Descrição
Sistema de gestão de atividades desenvolvido em Flask para controle e acompanhamento de tarefas em condomínios.

## Requisitos
- Python 3.11+
- pip (gerenciador de pacotes Python)
- Git (opcional, para controle de versão)

## Instalação

1. Clone o repositório:
```bash
git clone [URL_DO_REPOSITÓRIO]
cd site-m2d
```

2. Crie e ative o ambiente virtual:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
Create a `.env` file in the project root with the following variables:
```env
SECRET_KEY=sua_chave_secreta
DATABASE_URL=sqlite:///site.db
```

5. Inicialize o banco de dados:
```bash
flask db upgrade
```

6. Crie um usuário administrador:
```bash
python create_admin.py
```

## Executando o Projeto

1. Ative o ambiente virtual (se ainda não estiver ativo):
```bash
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. Execute o servidor:
```bash
python run.py
```

O servidor estará disponível em `http://localhost:5000`

## Estrutura do Projeto

```
site-m2d/
├── app/
│   ├── __init__.py          # Inicialização da aplicação
│   ├── models/              # Modelos do banco de dados
│   ├── routes/              # Rotas da aplicação
│   ├── forms/               # Formulários
│   ├── templates/           # Templates HTML
│   └── static/              # Static files (CSS, JS, images)
├── migrations/              # Migrações do banco de dados
├── logs/                    # Logs da aplicação
├── tests/                   # Testes automatizados
├── venv/                    # Ambiente virtual
├── .env                     # Variáveis de ambiente
├── requirements.txt         # Dependências do projeto
└── run.py                   # Main execution file
```

## Funcionalidades Principais

### Gestão de Usuários
- Registro de usuários
- Autenticação
- Níveis de acesso (admin, supervisor, normal)
- Recuperação de senha

### Gestão de Condomínios
- Cadastro de condomínios
- Ativação/desativação
- Atribuição de supervisores

### Gestão de Atividades
- Criação de atividades
- Atribuição de responsáveis
- Definição de prazos
- Acompanhamento de status
- Notificações automáticas

### Relatórios
- Exportação para Excel
- Estatísticas de atividades
- Filtros por período e condomínio

## Logs

O sistema mantém logs detalhados em `logs/site.log` com as seguintes informações:
- Data e hora
- Nível do log (INFO, WARNING, ERROR)
- Mensagem
- File and line where the log was generated

## Testes

Para executar os testes automatizados:
```bash
python -m pytest
```

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Suporte

Para reportar problemas ou solicitar novas funcionalidades, abra uma issue no repositório.

## Licença

This project is under the MIT license. See the `LICENSE` file for more details. 