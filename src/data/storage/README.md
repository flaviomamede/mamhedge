# Sistema de Armazenamento e Registro de Operações

## Descrição

Este módulo fornece o sistema de armazenamento para operações parseadas do robô EverHedge e o registro de decisões de investimento (conta real vs. simulada).

## Componentes

### 1. Models (`models.py`)

Define os modelos de dados para operações registradas:

- **`RegisteredOperation`**: Expande `TERFOperation` com campos de:
  - Decisão de investimento (status, tipo de conta, motivo)
  - Análise bayesiana (consenso, confiança ajustada)
  - Acompanhamento (custos, resultados, decisões diárias)
  - Validação final (lucro/prejuízo, confirmação bayesiana)

- **`OperationStatus`**: Enum com status possíveis:
  - `SUGERIDA`: Apenas parseada, ainda não analisada
  - `ANALISADA`: Analisada mas não investida
  - `INVESTIDA_REAL`: Investida em conta real
  - `INVESTIDA_SIMULADA`: Investida em conta simulada
  - `ENCERRADA`: Operação finalizada
  - `DESCARTADA`: Decisão de não investir

- **`AccountType`**: Tipo de conta (REAL ou SIMULADA)

- **`ConsensoLevel`**: Nível de consenso dos relatórios (FORTE, MEDIO, NULO, CONTRA)

- **`ConfiancaLevel`**: Nível de confiança ajustada (ALTA, MEDIA, BAIXA)

### 2. Database (`database.py`)

Sistema de armazenamento usando SQLite:

- **`OperationDatabase`**: Classe principal para gerenciar operações
  - `save_operation()`: Salva ou atualiza uma operação
  - `get_operation(id)`: Recupera operação por ID
  - `list_operations()`: Lista operações com filtros (status, conta_tipo)
  - `update_operation_status()`: Atualiza status de uma operação

## Fluxo de Uso

### 1. Parsear e Registrar Operações

```python
from src.data.parsers import EverHedgeParser
from src.data.storage import RegisteredOperation, OperationDatabase

# Parsear operações do robô
parser = EverHedgeParser()
with open('radar.md', 'r') as f:
    text = f.read()
terf_operations = parser.parse_all_operations(text)

# Criar banco de dados
db = OperationDatabase("mamhedge_operations.db")

# Registrar cada operação
for terf_op in terf_operations:
    reg_op = RegisteredOperation.from_terf_operation(terf_op)
    db.save_operation(reg_op)
```

### 2. Marcar Operação como Investida

```python
from src.data.storage import AccountType, ConsensoLevel, ConfiancaLevel

# Recuperar operação
op = db.get_operation(operation_id)

# Analisar consenso (exemplo - na prática você consultaria os relatórios)
op.consenso = ConsensoLevel.FORTE  # 3+ carteiras recomendam
op.confianca_ajustada = ConfiancaLevel.ALTA

# Decisão baseada no consenso
if op.consenso == ConsensoLevel.FORTE:
    op.marcar_investida(AccountType.REAL, "Consenso forte - 3+ carteiras")
else:
    op.marcar_investida(AccountType.SIMULADA, "Consenso médio - testando")

# Salvar decisão
db.save_operation(op)
```

### 3. Descartar Operação

```python
op.marcar_descartada("Rating baixo ou consenso contra")
db.save_operation(op)
```

### 4. Encerrar Operação com Resultado

```python
op.encerrar(
    lucro_prejuizo=150.50,  # R$ 150,50 de lucro
    status_final="GAIN",
    bayes_confirmou=True  # A análise bayesiana confirmou
)
db.save_operation(op)
```

### 5. Consultar Operações

```python
# Todas as operações
todas = db.list_operations()

# Apenas investidas em conta real
reais = db.list_operations(status=OperationStatus.INVESTIDA_REAL)

# Apenas investidas em conta simulada
simuladas = db.list_operations(status=OperationStatus.INVESTIDA_SIMULADA)

# Descartadas
descartadas = db.list_operations(status=OperationStatus.DESCARTADA)
```

## Estrutura do Banco de Dados

O banco SQLite (`mamhedge_operations.db`) contém uma tabela `operations` com:

- Campos de identificação: `id`, `estrategia`
- Campos bayesianos: `probabilidade_app`, `consenso`, `confianca_ajustada`
- Campos de decisão: `status`, `conta_tipo`, `data_decisao`, `motivo_decisao`
- Campos de monitoramento: `custo_montagem`, `alvo_saida`, `preco_atual`, etc.
- Campos de validação: `data_saida`, `lucro_prejuizo_real`, `status_final`, `bayes_confirmou`
- Dados da TERF: `operacao_terf_json` (JSON serializado)

## Integração com Análise Bayesiana

O sistema está preparado para integração com análise bayesiana:

1. **Entrada (Priori)**: `probabilidade_app` - probabilidade do app/robô
2. **Evidências**: `consenso` - nível de consenso dos relatórios
3. **Saída (Posteriori)**: `confianca_ajustada` - confiança ajustada após análise
4. **Validação**: `bayes_confirmou` - se a análise confirmou após resultado

## Scripts Disponíveis

### 1. `marcar_investimento.py`
Script interativo para marcar operações individuais como investidas.

### 2. `visualizar_operacoes.py`
Visualiza operações com vários filtros e opções de detalhamento.

### 3. `marcar_todas_simulada.py`
Marca todas as TERFs sugeridas como investidas em conta simulada e consulta preços atuais.

### 4. `marcar_travas_simulada.py`
Marca travas como investidas em conta simulada baseado em esperança estatística e consulta preços.

### 5. `alocar_e_atualizar_carteira.py` ⭐ **NOVO**
Script integrado que:
- Aloca capital entre TERFs e Travas (padrão: 95% TERFs, 5% Travas)
- Usa esperança estatística para alocar dentro de cada estratégia
- Consulta opcoes.net.br para atualizar preços
- Calcula lucro e margem considerando alocações
- Mostra resumo agrupado por TERFs e Travas

**Uso:**
```bash
python3 src/data/storage/alocar_e_atualizar_carteira.py \
  --capital 100000 \
  --pct-terfs 95 \
  --pct-travas 5
```

## Integração com Esperança Estatística

O sistema agora integra cálculo de esperança estatística para alocação inteligente:

- **TERFs**: Probabilidade baseada em rating, retorno baseado em rentabilidade
- **Travas**: Probabilidade baseada em distância do ativo e payoff
- **Alocação**: Proporcional à esperança estatística (EV)

Veja `../../analysis/` para detalhes sobre o sistema de esperança estatística.

## Exemplo Completo

Veja `exemplo_uso.py` para um exemplo completo de uso do sistema.

## Notas

- O banco de dados é criado automaticamente na primeira execução
- Operações são identificadas por UUID único
- Todas as datas são armazenadas em formato ISO
- A TERFOperation é serializada como JSON para armazenamento
- Preços são consultados automaticamente de opcoes.net.br
- Lucro e margem são calculados considerando as alocações

