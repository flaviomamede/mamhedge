# MamHedge - Sistema de Análise e Gestão de Investimentos em Opções

## Visão Geral

O **MamHedge** é um sistema integrado de análise de cenários, heurística de alternativas e gestão de operações estruturadas em opções. O projeto combina análise fundamentalista e técnica (via consenso de relatórios de carteiras), sugestões de operações do robô da EverHedge e inferência bayesiana para otimizar decisões de investimento em operações conservadoras (TERFs) e especulativas (Travas).

O robô da EverHedge fornece sugestões de operações estruturadas (travas) com estimativas de resultado, enquanto os relatórios de carteiras (XP, Empiricus, BTG, Bradesco) fornecem análise fundamentalista e técnica para indicar a tendência esperada dos ativos. O sistema cruza essas informações para decidir se uma oportunidade deve ser executada em conta real ou simulada.

## Objetivos

1. **Análise de Cenário**: Avaliação sistemática de oportunidades de mercado
2. **Heurística de Alternativas**: Filtragem e classificação de ativos candidatos baseada no consenso de relatórios
3. **Registro de Oportunidades**: Captura e armazenamento de sugestões do robô da EverHedge (travas com estimativas de resultado)
4. **Gestão de Contas**: Registro de aplicações em conta real e simulada, com decisão baseada na tendência indicada pelo consenso de relatórios
5. **Aprendizado Probabilístico**: Melhoria contínua da heurística através de análise bayesiana
6. **Registro de Manejos**: Histórico completo de operações e ajustes realizados
7. **Benchmarking**: Acompanhamento de rentabilidade comparativa ao CDI

## Arquitetura do Sistema

### Componentes Principais

#### 1. Análise de Cenário
- Avaliação de condições de mercado
- Identificação de tendências e reversões
- Análise de volatilidade implícita vs. histórica
- Classificação de oportunidades por qualidade

#### 2. Heurística de Alternativas
- **Filtro de Consenso**: Agregação de recomendações de múltiplas fontes
  - XP Investimentos
  - Empiricus
  - BTG Pactual
  - Bradesco
- **Análise dos Relatórios**: Os relatórios fornecem análise fundamentalista e técnica para compor carteiras de ações
- **Critério de Candidatura**: Ativos presentes em 2+ carteiras recomendadas
- **Classificação de Confiança**: Alta, Média, Baixa baseada no consenso e na tendência esperada

#### 3. Registro de Oportunidades (Robô EverHedge)
- Captura de sugestões de operações estruturadas (travas)
- Armazenamento de estimativas de resultado fornecidas pelo robô
- Estrutura da operação sugerida (opções, strikes, custos, payoffs estimados)
- Integração com filtro de consenso para decisão de execução (conta real vs. simulada)

#### 4. Gestão de Contas (Real e Simulada)
- **Decisão de Execução**: Baseada na tendência indicada pelo consenso de relatórios
  - Se o consenso confirma a tendência da operação sugerida → Conta Real
  - Se há divergência ou incerteza → Conta Simulada
- **Conta Simulada**: Ambiente de teste para validação de estratégias
  - Permite testar heurísticas sem risco
  - Coleta dados para análise bayesiana
  - Calibração de probabilidades esperadas vs. reais
- **Conta Real**: Execução de operações validadas pelo consenso
  - Registro completo de entradas e saídas
  - Rastreamento de custos operacionais
  - Análise de execução vs. expectativa

#### 5. Inferência Bayesiana
- **Probabilidade A Priori**: Dados históricos e estatísticas do aplicativo
- **Evidências**: Consenso de relatórios + sinal do robô
- **Probabilidade A Posteriori**: Probabilidade ajustada para cada operação específica
- **Calibração Contínua**: Atualização das probabilidades baseada em resultados reais

#### 6. Registro de Manejos
- Histórico de todas as operações realizadas
- Registro de ajustes e rolagens
- Análise de eficácia dos manejos
- Identificação de padrões de sucesso/falha

#### 7. Benchmarking e Rentabilidade
- Cálculo de rentabilidade global do portfólio
- Comparação com CDI (benchmark de referência)
- Análise de performance por estratégia (TERF vs. Travas)
- Métricas de risco-retorno ajustado

## Estratégias de Investimento

### TERF (Travas Estruturadas de Retorno Flexível/Fixo)
- **Perfil**: Conservadora
- **Objetivo**: Retorno superior ao CDI com risco controlado
- **Probabilidade Esperada**: 75-98% de sucesso
- **Retorno Alvo**: 2,5% (metade do potencial de 5%)
- **Filosofia**: "O Bom é inimigo do Ótimo" - saída antecipada em oportunidades

### Travas de Alta/Baixa
- **Perfil**: Especulativa
- **Objetivo**: Retornos assimétricos (perder pouco, ganhar muito)
- **Probabilidade Esperada**: 10-50% (ajustada pela heurística)
- **Retorno Alvo**: 500-1000% quando acerta
- **Filosofia**: Apostas convexas com risco limitado ao custo de montagem

## Sistema de Alocação de Capital (Vasos Comunicantes)

### Distribuição Inicial
- **Renda Fixa (LFTs/CDBs)**: 75% do capital
- **TERFs**: 95% do capital alocado em opções (padrão)
- **Travas**: 5% do capital alocado em opções (padrão)

### Alocação Dentro de Cada Estratégia

Dentro de cada estratégia (TERFs ou Travas), o capital é alocado baseado em **Esperança Estatística**:

- Operações com maior EV recebem mais capital
- Operações com EV negativo não recebem alocação
- Alocação é proporcional ao EV (não igual para todas)

### Regras de Fluxo

#### 1. Ignição (TERF → Trava)
- **Gatilho**: TERF render mais que 150% do CDI do período
- **Cálculo do Excedente**: `Funding = Lucro_Líquido_TERF - (Capital_Alocado × CDI × 1.5)`
- **Ação**: Excedente transfere para o pool de Travas

#### 2. Gestão de Travas
- **Em caso de GANHO**:
  - 50% retorna para patrimônio global (realização de lucro)
  - 50% permanece no pool de Travas (juros compostos no risco)
- **Em caso de PERDA**:
  - Perda limitada ao pool de Travas
  - **Regra de Ouro**: Nunca usar capital de Renda Fixa ou TERFs para cobrir perdas em Travas
  - Se o pool zerar, operações de Travas são suspensas até novo excedente de TERFs

#### 3. Rebalanceamento de TERFs
- **Expansão**: Aumento gradual de 25% para 30-35% baseado em:
  - Taxa de acerto > 85% (após 20+ operações)
  - Retorno médio acima do CDI
  - Consistência do sistema (robô + consenso)
- **Contração**: Redução para 25% (ou menos) se:
  - Taxa de acerto < 70%
  - Retornos abaixo do CDI
  - Condições de mercado adversas

## Estrutura de Dados

### Tabela Mestra de Operações

#### Bloco 1: Filtro Bayesiano (Entrada)
- ID da operação
- Ativo
- Estratégia (TERF/Trava Alta/Trava Baixa)
- Probabilidade do App (Priori)
- Consenso (Evidência 1): Forte/Médio/Nulo/Contra (tendência indicada pelos relatórios)
- Robô (Evidência 2): Sugestão de operação e estimativas de resultado
- Confiança Ajustada: Alta/Média/Baixa

#### Bloco 2: Execução e Monitoramento
- Custo de montagem
- Alvo de saída (R$)
- Preço atual (book)
- Resultado atual (%)
- Distância do alvo
- Decisão do dia

#### Bloco 3: Validação (Posteriori)
- Data de saída
- Lucro/Prejuízo real
- Status (GAIN/LOSS)
- Bayes: Confirmou? (Sim/Neutro/Não)

## Métricas e Análises

### Esperança Matemática (Expected Value)

O sistema utiliza esperança estatística para alocar capital de forma inteligente:

```
EV = (Probabilidade × Retorno_Positivo) + ((1 - Probabilidade) × Retorno_Negativo)
```

#### Para TERFs:
- **Probabilidade**: Baseada em rating (*** = 98%, ** = 90%, * = 80%)
- **Retorno Positivo**: Metade do potencial (2.5% se potencial é 5%)
- **Retorno Negativo**: Perda limitada (máximo um período de CDI)

#### Para Travas:
- **Probabilidade**: Estimada baseada em distância do ativo e payoff
- **Retorno Positivo**: Payoff da trava (%)
- **Retorno Negativo**: -100% (perde tudo, vira pó)

### Sistema de Alocação por Esperança Estatística

O sistema aloca capital proporcionalmente à esperança estatística:

1. **Calcula EV** para cada operação (TERF ou Trava)
2. **Filtra** apenas operações com EV positivo
3. **Aloca** capital proporcionalmente ao EV
4. **Prioriza** operações com maior EV, independente do payoff

**Exemplo**: Uma trava com payoff menor (800%) mas distância menor (5%) pode ter maior EV que uma trava com payoff maior (2400%) mas distância maior (10%).

### Atualização de Preços e Cálculo de Resultados

O sistema consulta automaticamente `opcoes.net.br` para:
- Obter preços atuais das opções
- Calcular variação de cada opção
- Calcular resultado da estrutura completa (TERF ou Trava)
- Calcular lucro e margem considerando as alocações

### Análise Bayesiana
- Comparação de probabilidade a priori vs. a posteriori
- Identificação de fatores que melhoram/degradam performance
- Calibração contínua do modelo

### Benchmarking
- Rentabilidade Global vs. CDI
- Performance por estratégia (TERFs vs. Travas)
- Análise de drawdown
- Métricas de Sharpe (futuro)

## Fluxo de Trabalho

1. **Coleta de Dados**
   - Captura de relatórios de carteiras (XP, Empiricus, BTG, Bradesco) - análise fundamentalista e técnica
   - Monitoramento de sugestões do robô EverHedge (travas com estimativas de resultado)
   - Análise de condições de mercado

2. **Filtragem e Classificação**
   - Identificação de ativos candidatos através do consenso de relatórios
   - Cruzamento da tendência do consenso com a sugestão do robô
   - Cálculo de probabilidade ajustada (Bayesiana)

3. **Decisão de Entrada**
   - Avaliação de risco-retorno baseada no consenso e na sugestão do robô
   - Determinação de tamanho de posição (Critério de Kelly simplificado)
   - Decisão de execução: conta real (se consenso confirma) ou simulada (se há divergência/incerteza)

4. **Monitoramento**
   - Acompanhamento diário de posições
   - Avaliação de oportunidades de saída
   - Decisão de manejo (rolagem, ajuste, encerramento)

5. **Análise e Aprendizado**
   - Registro de resultados
   - Atualização de probabilidades bayesianas
   - Refinamento da heurística
   - Ajuste de alocação de capital

## Tecnologias e Ferramentas

- **Linguagem**: Python (principal)
- **Análise de Dados**: Pandas, NumPy
- **Inferência Bayesiana**: PyMC, scipy.stats
- **Visualização**: Matplotlib, Plotly
- **Armazenamento**: Banco de dados (SQLite/PostgreSQL) ou arquivos estruturados (CSV/Parquet)
- **APIs**: Integração com corretoras, BCB, fontes de dados de mercado

## Estrutura de Diretórios (Proposta)

```
mamhedge/
├── README.md
├── ideia.md
├── src/
│   ├── analysis/
│   │   ├── scenario_analysis.py
│   │   ├── heuristics.py
│   │   └── bayesian_inference.py
│   ├── data/
│   │   ├── collectors/
│   │   │   ├── everhedge_robot.py
│   │   │   ├── portfolio_reports.py
│   │   │   └── market_data.py
│   │   └── storage/
│   │       ├── database.py
│   │       └── models.py
│   ├── strategies/
│   │   ├── terf.py
│   │   ├── spreads.py
│   │   └── position_sizing.py
│   ├── monitoring/
│   │   ├── portfolio_tracker.py
│   │   ├── benchmark.py
│   │   └── performance_metrics.py
│   └── utils/
│       ├── config.py
│       └── helpers.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── results/
├── notebooks/
│   ├── exploratory_analysis.ipynb
│   ├── bayesian_calibration.ipynb
│   └── performance_analysis.ipynb
├── tests/
│   ├── test_heuristics.py
│   ├── test_bayesian.py
│   └── test_strategies.py
└── requirements.txt
```

## Próximos Passos

1. **Fase 1 - Fundação**
   - Estruturação do projeto
   - Implementação de coleta de dados básica
   - Criação da tabela mestra de operações

2. **Fase 2 - Análise**
   - Implementação de heurística de consenso
   - Integração com robô EverHedge
   - Sistema de análise bayesiana básico

3. **Fase 3 - Execução**
   - Sistema de registro de operações
   - Monitoramento de posições
   - Gestão de manejos

4. **Fase 4 - Otimização**
   - Calibração bayesiana avançada
   - Sistema de benchmarking
   - Dashboard de performance

5. **Fase 5 - Automação**
   - Alertas automáticos
   - Sugestões de entrada/saída
   - Relatórios periódicos

## Princípios Fundamentais

1. **Disciplina**: Só entrar quando múltiplos filtros confirmam
2. **Proteção de Capital**: Nunca comprometer o patrimônio principal
3. **Aprendizado Contínuo**: Cada operação é uma oportunidade de melhorar o modelo
4. **Transparência**: Registro completo de todas as decisões e resultados
5. **Paciência**: Estudos de longo prazo requerem consistência

## Referências

- Documentação conceitual: `ideia.md`
- Análise de opções: Modelos Black-Scholes, Heston
- Inferência Bayesiana: Teorema de Bayes, MCMC
- Gestão de Risco: Critério de Kelly, Value at Risk (VaR)

## Licença

Este projeto é de uso pessoal e educacional.

---

**Nota**: Este sistema é uma ferramenta de apoio à decisão. Investimentos em opções envolvem risco significativo. Sempre consulte profissionais qualificados e invista apenas o que pode perder.

