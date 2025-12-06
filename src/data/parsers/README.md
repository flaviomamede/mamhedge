# Parsers do Robô EverHedge

## Descrição

Este módulo contém os parsers para processar dados do robô da EverHedge copiados em formato texto:
- **TERFs** (Travas Estruturadas de Retorno Flexível): Operações conservadoras
- **Travas**: Operações especulativas (Bear Put Spread, Bull Call Spread)

## Estrutura de Dados

O parser extrai as seguintes informações de cada operação TERF:

### Campos Extraídos

- **Ação**: Código da ação de referência (ex: ITUB4)
- **Preço**: Preço da ação negociada
- **Data**: Data de busca do radar
- **Call (Vendida)**:
  - Código da Call
  - Strike da Call
  - Vencimento da Call
  - Valor negociado da Call
- **Put (Comprada)**:
  - Código da Put
  - Strike da Put
  - Vencimento da Put
  - Valor negociado da Put
- **Coeficiente**: Coeficiente total da estrutura TERF
- **Rentabilidade**:
  - Miolo: Rentabilidade do miolo no vencimento da opção curta
  - Cima: Rentabilidade para cima até vencimento da opção longa
  - Baixo: Rentabilidade para baixo até vencimento da opção longa
- **Meses**: Número de meses até vencimento da Put
- **CDI Período**: CDI do período até vencimento da Put
- **Rating**: Classificação da estrutura (* = Boa, ** = Muito Boa, *** = Excelente)
- **Tipo**: Tipo da operação (ex: U)

## Uso

```python
from src.data.parsers import EverHedgeParser

# Lê o texto copiado do robô
with open('radar.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Cria o parser
parser = EverHedgeParser()

# Parse todas as operações
operations = parser.parse_all_operations(text)

# Processa cada operação
for op in operations:
    print(f"Ação: {op.acao}")
    print(f"Rentabilidade Miolo: {op.rentabilidade_miolo}%")
    # ...
```

## Notas de Implementação

- O parser aceita formatos com ou sem espaços após ":"
- Valores monetários usam vírgula como separador decimal (formato brasileiro)
- Datas no formato DD/MM/YYYY
- Rentabilidades são extraídas das 3 linhas seguintes a "Rentabilidade:"

## Parser de Travas

O módulo também inclui `TravaParser` para processar operações de travas (spreads):

### Campos Extraídos para Travas

- **Ação**: Código da ação de referência
- **Preço**: Valor de referência da ação
- **Data**: Data de busca da trava
- **Opção Comprada (C)**:
  - Código da opção
  - Strike
  - Valor negociado
- **Opção Vendida (V)**:
  - Código da opção
  - Strike
  - Valor negociado
- **Distância do Ativo**: Distância do valor do ativo com o primeiro strike
- **Custo Total**: Valor total da trava
- **Payoff**: Payoff máximo da operação (%)

### Uso do Parser de Travas

```python
from src.data.parsers import TravaParser

# Lê o texto copiado do robô
with open('radar.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Cria o parser
parser = TravaParser()

# Parse todas as travas
travas = parser.parse_all_operations(text)

# Processa cada trava
for trava in travas:
    print(f"Ação: {trava.acao}")
    print(f"Payoff: {trava.payoff}%")
    print(f"Distância: {trava.distancia_ativo}%")
    # ...
```

## Status

✅ **Funcional**: Ambos os parsers estão completos e funcionais:
- ✅ Parser de TERFs: Extrai todos os campos corretamente, incluindo rentabilidades
- ✅ Parser de Travas: Extrai todos os campos, incluindo payoff em formato brasileiro (2.400,00%)

## Integração com Sistema de Armazenamento

Após parsear as operações, você pode registrá-las no banco de dados:

```python
from src.data.storage import RegisteredOperation, OperationDatabase

db = OperationDatabase("mamhedge_operations.db")

# Para TERFs
for terf_op in terf_operations:
    reg_op = RegisteredOperation.from_terf_operation(terf_op)
    db.save_operation(reg_op)

# Para Travas (criar RegisteredOperation manualmente)
# Veja scripts em ../storage/ para exemplos
```

Veja `../storage/README.md` para mais detalhes sobre o sistema de armazenamento.

