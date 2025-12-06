# Como Usar o Sistema MamHedge

## Guia Rápido

### 1. Parsear Operações do Robô

Primeiro, copie o texto do robô da EverHedge e salve em `radar.md`, depois:

```bash
cd mamhedge
python3 src/data/parsers/everhedge_parser.py
```

Isso parseia as operações, mas ainda não as salva no banco. Para salvar:

```python
from src.data.parsers import EverHedgeParser
from src.data.storage import RegisteredOperation, OperationDatabase

# Parsear
parser = EverHedgeParser()
with open('radar.md', 'r') as f:
    text = f.read()
operations = parser.parse_all_operations(text)

# Salvar no banco
db = OperationDatabase("mamhedge_operations.db")
for terf_op in operations:
    reg_op = RegisteredOperation.from_terf_operation(terf_op)
    db.save_operation(reg_op)
```

### 2. Marcar Operação como Investida

**Opção A: Script Interativo (Recomendado)**

```bash
cd mamhedge
python3 src/data/storage/marcar_investimento.py
```

O script vai:
1. Listar todas as operações sugeridas
2. Você escolhe qual marcar
3. Pergunta sobre consenso (Forte/Médio/Nulo/Contra)
4. Pergunta sobre confiança ajustada (Alta/Média/Baixa)
5. Você decide: Conta Real, Conta Simulada ou Descartar

**Opção B: Código Python**

```python
from src.data.storage import OperationDatabase, AccountType, ConsensoLevel, ConfiancaLevel

db = OperationDatabase("mamhedge_operations.db")
op = db.get_operation(operation_id)

# Define consenso e confiança
op.consenso = ConsensoLevel.FORTE  # ou MEDIO, NULO, CONTRA
op.confianca_ajustada = ConfiancaLevel.ALTA  # ou MEDIA, BAIXA

# Marca como investida
op.marcar_investida(AccountType.REAL, "Consenso forte - 3+ carteiras")
# ou
op.marcar_investida(AccountType.SIMULADA, "Testando em simulada")

# Salva
db.save_operation(op)
```

### 3. Visualizar Operações

**Opção A: Script de Visualização**

```bash
# Ver todas as operações
python3 src/data/storage/visualizar_operacoes.py

# Ver apenas investidas em conta real
python3 src/data/storage/visualizar_operacoes.py --status investida_real

# Ver apenas investidas em conta simulada
python3 src/data/storage/visualizar_operacoes.py --status investida_simulada

# Ver com detalhes completos
python3 src/data/storage/visualizar_operacoes.py --detalhes

# Ver resumo geral
python3 src/data/storage/visualizar_operacoes.py --resumo

# Ver operação específica por ID
python3 src/data/storage/visualizar_operacoes.py --id abc123...
```

**Opção B: Código Python**

```python
from src.data.storage import OperationDatabase, OperationStatus, AccountType

db = OperationDatabase("mamhedge_operations.db")

# Todas as operações
todas = db.list_operations()

# Apenas investidas em conta real
reais = db.list_operations(status=OperationStatus.INVESTIDA_REAL)

# Apenas investidas em conta simulada
simuladas = db.list_operations(status=OperationStatus.INVESTIDA_SIMULADA)

# Operação específica
op = db.get_operation(operation_id)
```

### 4. Atualizar Rendimento (Consultar opcoes.net.br)

**Opção A: Script Interativo (Recomendado)**

```bash
cd mamhedge
python3 src/data/collectors/atualizar_rendimento.py
```

O script vai:
1. Listar todas as operações investidas (real e simulada)
2. Você escolhe qual atualizar
3. Escolhe se quer atualizar a Call ou a Put
4. Consulta automaticamente o site opcoes.net.br
5. Atualiza o preço e calcula o rendimento

**Opção B: Código Python**

```python
from src.data.collectors import OpcoesNetCollector
from src.data.storage import OperationDatabase

collector = OpcoesNetCollector()
db = OperationDatabase("mamhedge_operations.db")

# Busca operação
op = db.get_operation(operation_id)

# Consulta preço atual da Call (exemplo: PETRL311)
data = collector.get_option_data("PETRL311")

if data and 'preco_atual' in data:
    preco_atual = data['preco_atual']
    preco_compra = op.operacao_terf.valor_call
    
    # Calcula rendimento
    rendimento = collector.calcular_rendimento(preco_compra, preco_atual)
    
    # Atualiza operação
    op.preco_atual = preco_atual
    op.resultado_atual_pct = rendimento['variacao_pct']
    db.save_operation(op)
    
    print(f"Rendimento: {rendimento['variacao_pct']:+.2f}%")
```

## Fluxo Completo de Uso

### Dia 1: Parsear e Decidir

1. Copie o texto do robô para `radar.md`
2. Execute o parser para extrair operações
3. Salve no banco de dados
4. Execute `marcar_investimento.py` para decidir quais investir

### Dia 2 em diante: Acompanhar

1. Execute `atualizar_rendimento.py` para consultar preços atuais
2. Execute `visualizar_operacoes.py` para ver o status
3. Repita conforme necessário

### Quando Encerrar

```python
from src.data.storage import OperationDatabase

db = OperationDatabase("mamhedge_operations.db")
op = db.get_operation(operation_id)

# Encerra com resultado
op.encerrar(
    lucro_prejuizo=150.50,  # R$ 150,50 de lucro
    status_final="GAIN",
    bayes_confirmou=True  # A análise confirmou
)

db.save_operation(op)
```

## Exemplo Prático

### Exemplo: PETRL311

1. **Parsear**: Operação parseada e salva como `SUGERIDA`

2. **Decidir**: 
   ```bash
   python3 src/data/storage/marcar_investimento.py
   # Escolhe a operação
   # Consenso: Forte
   # Confiança: Alta
   # Decisão: Conta Real
   ```

3. **Acompanhar (uma semana depois)**:
   ```bash
   python3 src/data/collectors/atualizar_rendimento.py
   # Escolhe a operação
   # Escolhe Call: PETRL311
   # Sistema consulta https://opcoes.net.br/PETRL311
   # Atualiza preço e calcula rendimento
   ```

4. **Visualizar**:
   ```bash
   python3 src/data/storage/visualizar_operacoes.py --status investida_real --detalhes
   ```

### Exemplo: Marcar Todas em Simulada e Ver Resultado

Se você decidiu investir em **todas** as operações em conta simulada e quer ver o resultado após o fechamento do pregão:

```bash
python3 src/data/storage/marcar_todas_simulada.py
```

Este script:
1. ✅ Marca todas as operações sugeridas como investidas em conta simulada
2. 🔍 Consulta automaticamente o opcoes.net.br para cada Call e Put
3. 📊 Calcula o resultado de cada estrutura TERF completa
4. 📈 Gera relatório com:
   - Variação de cada Call
   - Variação de cada Put
   - Resultado da estrutura completa (TERF)
   - Estatísticas gerais (quantas deram lucro, etc.)

**Exemplo de saída:**
```
OPERAÇÃO 1: ITUB4
Call ITUBA434: ✅ +5.23%
Put ITUBX43: ✅ +2.15%
Estrutura TERF: 💰 R$ +15.50 (+3.45%)

OPERAÇÃO 2: BBAS3
Call BBASL235: 📉 -1.20%
Put BBASO230: ✅ +0.85%
Estrutura TERF: 📉 R$ -2.30 (-0.50%)

ESTATÍSTICAS
Calls com lucro: 2/4
Puts com lucro: 3/4
Estruturas com lucro: 2/4
💰 Lucro total das estruturas: R$ +13.20
```

## Estrutura de Arquivos

```
mamhedge/
├── radar.md                          # Texto copiado do robô
├── mamhedge_operations.db            # Banco SQLite (criado automaticamente)
├── src/
│   └── data/
│       ├── parsers/
│       │   └── everhedge_parser.py   # Parser do robô
│       ├── storage/
│       │   ├── marcar_investimento.py # Script para marcar investimentos
│       │   └── visualizar_operacoes.py # Script para visualizar
│       └── collectors/
│           ├── opcoes_net.py          # Coletor do opcoes.net.br
│           └── atualizar_rendimento.py # Script para atualizar rendimento
└── COMO_USAR.md                      # Este arquivo
```

### Exemplo: Alocação e Atualização Completa da Carteira ⭐ **RECOMENDADO**

O script mais completo que faz tudo automaticamente:

```bash
python3 src/data/storage/alocar_e_atualizar_carteira.py \
  --capital 100000 \
  --pct-terfs 95 \
  --pct-travas 5
```

Este script:
1. ✅ Parseia todas as TERFs e Travas do radar.md
2. 📊 Calcula esperança estatística (EV) para cada operação
3. 💰 Aloca capital proporcionalmente ao EV:
   - 95% do capital em TERFs (distribuído por EV)
   - 5% do capital em Travas (distribuído por EV)
4. 🔍 Consulta opcoes.net.br para cada opção
5. 📈 Calcula lucro e margem considerando alocações
6. 📋 Gera resumo agrupado:
   - Resumo de TERFs (capital, lucro, margem)
   - Resumo de Travas (capital, lucro, margem)
   - Resumo geral da carteira

**Exemplo de saída:**
```
💰 RESUMO GERAL DA CARTEIRA:
   Capital Total Alocado: R$ 100.000,00
      TERFs: R$ 95.000,00 (95.0%)
      Travas: R$ 5.000,00 (5.0%)

   💰 Lucro Total: R$ +2.500,00
      TERFs: R$ +2.000,00
      Travas: R$ +500,00
   💰 Margem Total: +2.50%
```

**Parâmetros:**
- `--capital`: Capital total (padrão: 100000)
- `--pct-terfs`: % para TERFs (padrão: 95)
- `--pct-travas`: % para Travas (padrão: 5)
- `--alpha-terf`: Alpha heurística TERFs (padrão: 1.0)
- `--alpha-trava`: Alpha heurística Travas (padrão: 1.5)

### Exemplo: Marcar Travas com Esperança Estatística

Se você tem travas no `radar.md` e quer alocar baseado em esperança estatística:

```bash
python3 src/data/storage/marcar_travas_simulada.py
```

Este script:
1. ✅ Parseia **TODAS** as travas do radar.md (não filtra por payoff)
2. 📊 Calcula esperança estatística para cada trava
3. 💰 Aloca capital proporcionalmente ao EV
4. 💾 Marca travas com EV positivo como investidas em conta simulada
5. 📊 Consulta opcoes.net.br para cada opção (comprada e vendida)
6. 📈 Calcula a margem após fechamento do pregão
7. 📋 Gera relatório completo com:
   - Probabilidade estimada e EV de cada trava
   - Alocação de capital
   - Variação de cada opção
   - Resultado da trava completa
   - Margem total e percentual

**Importante**: Travas com payoff menor podem receber mais capital se tiverem maior esperança estatística (maior probabilidade devido à menor distância do ativo).

## Sistema de Esperança Estatística

O sistema utiliza esperança estatística para alocar capital de forma inteligente:

### Para TERFs:
- **Probabilidade**: Baseada em rating (*** = 98%, ** = 90%, * = 80%)
- **Retorno Positivo**: Metade do potencial (2.5% se potencial é 5%)
- **Retorno Negativo**: Perda limitada (máximo um período de CDI)
- **EV**: `(Prob × Retorno_Positivo) + ((1-Prob) × Retorno_Negativo)`

### Para Travas:
- **Probabilidade**: Estimada baseada em distância do ativo e payoff
- **Retorno Positivo**: Payoff da trava (%)
- **Retorno Negativo**: -100% (perde tudo)
- **EV**: `(Prob × Payoff) + ((1-Prob) × -100%)`

### Alocação:
- Capital é alocado proporcionalmente ao EV
- Operações com maior EV recebem mais capital
- Operações com EV negativo não recebem alocação

**Exemplo**: Uma trava com payoff 800% e distância 5% pode ter maior EV (e receber mais capital) que uma trava com payoff 2400% e distância 10%.

## Cálculo de Lucro e Margem

O sistema consulta automaticamente `opcoes.net.br` para:
- Obter preços atuais das opções
- Calcular variação de cada opção
- Calcular resultado da estrutura completa (TERF ou Trava)
- Calcular lucro e margem considerando as alocações de capital

**Importante**: Os cálculos de lucro e margem são baseados nos preços reais consultados de opcoes.net.br após o fechamento do pregão.

## Dependências

```bash
pip install requests beautifulsoup4
```

## Notas

- O banco de dados é criado automaticamente na primeira execução
- Os scripts são interativos e guiam você passo a passo
- O coletor do opcoes.net.br pode falhar se o site mudar o formato
- Sempre verifique os dados antes de tomar decisões importantes
- A alocação baseada em esperança estatística prioriza operações com maior EV, não apenas maior payoff

