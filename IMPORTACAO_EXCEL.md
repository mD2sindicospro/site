# Importação de Atividades via Excel

Esta funcionalidade permite importar múltiplas atividades de uma vez através de um arquivo Excel.

## Como Usar

### 1. Acessar a Funcionalidade
- Faça login como administrador ou supervisor
- Vá para a página de listagem de atividades
- Clique no botão "Importar Excel" no cabeçalho

### 2. Baixar o Template
- Na página de importação, clique em "Baixar Template Excel"
- O arquivo será baixado com a estrutura correta e exemplos

### 3. Preparar o Arquivo Excel
O arquivo deve conter as seguintes colunas:

| Coluna | Obrigatória | Descrição | Exemplo |
|--------|-------------|-----------|---------|
| `titulo` | Sim | Título da atividade | "Limpeza da área comum" |
| `descricao` | Sim | Descrição detalhada | "Realizar limpeza completa da área comum incluindo corredores" |
| `condominio` | Sim | Nome do condomínio | "Residencial Exemplo" |
| `responsavel` | Sim | Nome do responsável | "João Silva" |
| `data_entrega` | Sim | Data de entrega | "31/12/2024" (formato DD/MM/AAAA) |

### 4. Importar o Arquivo
- Selecione o arquivo Excel preparado
- Clique em "Importar Atividades"
- Aguarde o processamento
- Verifique os resultados na tela de resumo

## Formato de Data
- DD/MM/AAAA (formato brasileiro, ex: 31/12/2024)

## Status das Atividades Importadas
- Todas as atividades importadas são criadas com status "Em Andamento"
- Se a data de entrega for no passado, o status será automaticamente "Atrasada"

## Validações

### Obrigatórias
- Título deve ter pelo menos 3 caracteres
- Descrição deve ter pelo menos 10 caracteres
- Condomínio deve existir no sistema
- Responsável deve existir no sistema
- Data de entrega deve ser válida

### Automáticas
- Todas as atividades são criadas com status "Em Andamento"
- Se a data de entrega for no passado, o status será automaticamente definido como "Atrasada"
- O sistema busca condomínios e responsáveis por correspondência parcial (case-insensitive)

## Tratamento de Erros

### Tipos de Erro
1. **Arquivo inválido**: Formato não suportado ou arquivo corrompido
2. **Colunas ausentes**: Arquivo não contém todas as colunas obrigatórias
3. **Dados inválidos**: Valores que não atendem às validações
4. **Entidades não encontradas**: Condomínio ou responsável inexistente
5. **Erros de banco**: Problemas ao salvar no banco de dados

### Relatório de Erros
- O sistema gera um relatório detalhado com todos os erros encontrados
- Cada erro indica a linha específica do arquivo
- Atividades válidas são importadas mesmo se houver erros em outras linhas

## Exemplo de Arquivo Excel

| titulo | descricao | condominio | responsavel | data_entrega |
|--------|-----------|------------|-------------|--------------|
| Limpeza da área comum | Realizar limpeza completa da área comum incluindo corredores e hall de entrada | Residencial Exemplo | João Silva | 31/12/2024 |
| Manutenção do elevador | Verificar funcionamento do elevador e realizar manutenção preventiva | Residencial Exemplo | Maria Santos | 31/12/2024 |
| Verificação do sistema de incêndio | Testar sistema de incêndio e verificar extintores | Residencial Exemplo | Pedro Oliveira | 31/12/2024 |

## Dicas Importantes

1. **Nomes exatos**: Os nomes de condomínios e responsáveis devem corresponder exatamente aos cadastrados no sistema
2. **Use o template**: Sempre use o template fornecido como base
3. **Verifique as datas**: Certifique-se de que as datas estão no formato DD/MM/AAAA
4. **Evite caracteres especiais**: Use apenas caracteres ASCII nos títulos e descrições
5. **Teste com poucos dados**: Comece com um arquivo pequeno para testar

## Permissões

- Apenas administradores e supervisores podem importar atividades
- Cada atividade importada será criada pelo usuário que fez a importação
- As atividades seguem o mesmo fluxo de notificações das atividades criadas manualmente

## Suporte

Em caso de problemas:
1. Verifique se o arquivo está no formato correto
2. Confirme se os nomes de condomínios e responsáveis estão corretos
3. Verifique o relatório de erros detalhado
4. Entre em contato com o suporte técnico se necessário 