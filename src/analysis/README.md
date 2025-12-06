# Módulo de Análise - Esperança Estatística

## Descrição

Este módulo implementa o sistema de cálculo de esperança estatística (Expected Value) e alocação de capital para operações estruturadas em opções (TERFs e Travas).

## Componentes

### 1. Esperança Estatística para Travas (`esperanca_estatistica.py`)

Calcula esperança estatística e aloca capital entre travas baseado em:
- **Probabilidade**: Estimada baseada em distância do ativo e payoff
- **Retorno Positivo**: Payoff da trava (%)
- **Retorno Negativo**: -100% (perde tudo)

**Fórmula:**
```
EV = (Probabilidade × Payoff) + ((1 - Probabilidade) × -100%)
```

**Uso:**
```python
from src.analysis import calcular_alocacao_travas
from src.data.parsers import TravaParser

# Parse travas
parser = TravaParser()
travas = parser.parse_all_operations(text)

# Calcula alocações
alocacoes = calcular_alocacao_travas(
    travas,
    capital_total=1000.0,
    alpha_heuristica=1.5,  # Acredita que robô melhora prob em 50%
    metodo="proporcional"
)

# Alocações são proporcionais ao EV
for aloc in alocacoes:
    if aloc.alocacao_valor > 0:
        print(f"{aloc.trava.acao}: EV {aloc.esperanca_estatistica:+.2f}%, Alocação: {aloc.alocacao_pct:.2f}%")
```

### 2. Esperança Estatística para TERFs (`esperanca_terf.py`)

Calcula esperança estatística e aloca capital entre TERFs baseado em:
- **Probabilidade**: Baseada em rating (*** = 98%, ** = 90%, * = 80%)
- **Retorno Positivo**: Metade do potencial (2.5% se potencial é 5%)
- **Retorno Negativo**: Perda limitada (máximo um período de CDI)

**Fórmula:**
```
EV = (Probabilidade × Retorno_Positivo) + ((1 - Probabilidade) × Retorno_Negativo)
```

**Uso:**
```python
from src.analysis import calcular_alocacao_terfs
from src.data.parsers import EverHedgeParser

# Parse TERFs
parser = EverHedgeParser()
terfs = parser.parse_all_operations(text)

# Calcula alocações
alocacoes = calcular_alocacao_terfs(
    terfs,
    capital_total=95000.0,
    alpha_heuristica=1.0,  # TERFs já são conservadoras
    metodo="proporcional"
)

# Alocações são proporcionais ao EV
for aloc in alocacoes:
    if aloc.alocacao_valor > 0:
        print(f"{aloc.terf.acao}: EV {aloc.esperanca_estatistica:+.2f}%, Alocação: {aloc.alocacao_pct:.2f}%")
```

### 3. Script de Alocação de Travas (`alocar_travas.py`)

Script de linha de comando para calcular alocações de travas:

```bash
python3 src/analysis/alocar_travas.py \
  --capital 1000 \
  --alpha 1.5 \
  --payoff-min 0 \
  --metodo proporcional
```

**Parâmetros:**
- `--capital`: Capital total disponível
- `--alpha`: Alpha heurística (1.0 = mercado, 1.5 = robô melhora 50%)
- `--payoff-min`: Filtro mínimo de payoff (0 = todas)
- `--metodo`: Método de alocação (proporcional, kelly, equal_risk)

## Conceitos

### Esperança Estatística (Expected Value)

A esperança estatística é o valor esperado de uma operação considerando todos os cenários possíveis:

```
EV = Σ (Probabilidade_i × Resultado_i)
```

Para operações binárias (ganha ou perde):
```
EV = (Prob × Retorno_Positivo) + ((1 - Prob) × Retorno_Negativo)
```

### Alocação Proporcional

O capital é alocado proporcionalmente à esperança estatística:

```
Alocação_i = (EV_i / Σ EV_positivos) × Capital_Total
```

Isso garante que operações com maior EV recebam mais capital.

### Alpha Heurística

Fator de ajuste que reflete a confiança na heurística (robô + consenso):

- **Alpha = 1.0**: Usa probabilidade implícita do mercado
- **Alpha = 1.5**: Acredita que robô melhora probabilidade em 50%
- **Alpha = 2.0**: Acredita que robô dobra a probabilidade

## Integração

O sistema de análise é integrado com:
- **Parsers**: Para obter dados das operações
- **Storage**: Para salvar alocações e resultados
- **Collectors**: Para consultar preços atuais e calcular resultados

Veja `../data/storage/alocar_e_atualizar_carteira.py` para exemplo de uso integrado.

