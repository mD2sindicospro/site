# Sistema de Limpeza Automática - Primeiro Acesso do Dia

## 📋 Visão Geral

O sistema implementa uma rotina automática para limpar mensagens antigas do banco de dados no primeiro acesso do dia, mantendo o sistema otimizado e evitando acúmulo desnecessário de dados.

## 🚀 Funcionalidades

### ✅ Limpeza Automática
- **Frequência**: No primeiro acesso do dia
- **Critério**: Remove mensagens com mais de 20 dias
- **Segurança**: Apenas mensagens antigas são removidas
- **Logs**: Todas as operações são registradas
- **Controle**: Arquivo `last_cleanup.txt` para controle de execução

### ✅ Execução Transparente
- **Automático**: Executa sem intervenção do usuário
- **Eficiente**: Apenas uma vez por dia
- **Discreto**: Não requer interface administrativa

## 🛠️ Componentes Implementados

### 1. **Sistema de Controle** (`app/scheduler.py`)
```python
# Controle de execução diária
def should_run_cleanup():
    last_cleanup = get_last_cleanup_date()
    today = datetime.now().date()
    return last_cleanup is None or last_cleanup != today
```

### 2. **Função de Limpeza**
```python
def cleanup_old_messages():
    cutoff_date = datetime.now() - timedelta(days=20)
    old_messages = Message.query.filter(
        Message.created_at < cutoff_date
    ).all()
    # Remove mensagens antigas
```

### 3. **Middleware de Verificação**
- Execução automática no primeiro acesso
- Controle via arquivo `last_cleanup.txt`
- Logs transparentes

## 📊 Controle de Execução

- **Arquivo de Controle**: `last_cleanup.txt`
- **Data da Última Execução**: Registrada automaticamente
- **Verificação Diária**: No primeiro acesso do dia
- **Limite de Retenção**: 20 dias

## 🔧 Configuração

### Dependências
Nenhuma dependência adicional necessária - usa apenas bibliotecas padrão do Python.

### Inicialização Automática
A verificação é executada automaticamente no middleware de requisições:

```python
# app/__init__.py
@app.before_request
def before_request():
    from app.scheduler import check_and_cleanup
    check_and_cleanup()
```

## 🧪 Testes

### Script de Teste
```bash
python test_scheduler.py
```

### Teste Manual
1. Execute `python test_scheduler.py`
2. Verifique os logs da aplicação
3. Monitore o arquivo `last_cleanup.txt`

## 📝 Logs

Todas as operações são registradas:
```
INFO: Limpeza automática: 15 mensagens antigas removidas
INFO: Scheduler iniciado com sucesso
ERROR: Erro na limpeza automática de mensagens: [erro]
```

## ⚙️ Configurações Avançadas

### Alterar Período de Retenção
```python
# Em app/scheduler.py
cutoff_date = datetime.now() - timedelta(days=30)  # 30 dias
```

### Alterar Arquivo de Controle
```python
# Em app/scheduler.py
CLEANUP_LOG_FILE = 'meu_arquivo_controle.txt'
```

### Desabilitar Temporariamente
```python
# Em app/__init__.py - comentar a linha:
# check_and_cleanup()
```

## 🚨 Considerações de Segurança

- ✅ **Apenas mensagens antigas**: Critério rigoroso de 20 dias
- ✅ **Logs completos**: Rastreabilidade de todas as operações
- ✅ **Rollback automático**: Em caso de erro, transação é revertida
- ✅ **Acesso restrito**: Apenas admins podem executar manualmente

## 📈 Benefícios

1. **Performance**: Banco de dados mais leve
2. **Custos**: Menor uso de armazenamento
3. **Manutenção**: Limpeza automática sem intervenção
4. **Segurança**: Preservação de dados recentes
5. **Monitoramento**: Controle total via interface web

## 🔄 Fluxo de Funcionamento

1. **Primeiro Acesso**: Usuário acessa qualquer página
2. **Verificação**: Sistema verifica se já foi executada hoje
3. **Execução**: Se necessário, remove mensagens >20 dias
4. **Controle**: Registra data da execução
5. **Log**: Registra operação nos logs
6. **Transparência**: Usuário não percebe a execução

## 🛡️ Tratamento de Erros

- **Exceções capturadas**: Erros não interrompem o scheduler
- **Rollback automático**: Transações são revertidas em caso de erro
- **Logs detalhados**: Rastreabilidade completa
- **Recuperação**: Scheduler continua funcionando após erros

---

**Desenvolvido para o Sistema de Gestão de Atividades M2D** 🏢 