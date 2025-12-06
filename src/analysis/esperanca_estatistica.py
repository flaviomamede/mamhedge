"""
Sistema de cálculo de Esperança Estatística e alocação de capital para travas.

Baseado na discussão do ideia.md:
EV = (Probabilidade × Retorno_Positivo) + ((1 - Probabilidade) × Retorno_Negativo)

Para travas:
- Retorno Positivo = Payoff (%)
- Retorno Negativo = -100% (perde tudo, vira pó)
- Probabilidade = estimada baseada na distância do ativo e payoff
"""

import math
from typing import List, Dict, Optional
from dataclasses import dataclass
from ..data.parsers.trava_parser import TravaOperation


@dataclass
class AlocacaoTrava:
    """Alocação calculada para uma trava."""
    trava: TravaOperation
    probabilidade_estimada: float  # Probabilidade estimada de sucesso (%)
    esperanca_estatistica: float  # Esperança estatística (EV)
    alocacao_pct: float  # Porcentagem do capital total a alocar
    alocacao_valor: float  # Valor em R$ a alocar
    retorno_esperado: float  # Retorno esperado em R$


class EsperancaEstatistica:
    """
    Calcula esperança estatística e aloca capital entre travas.
    
    A probabilidade é estimada baseada em:
    - Distância do ativo (quanto maior, menor a probabilidade)
    - Payoff (quanto maior, menor a probabilidade implícita do mercado)
    """
    
    def __init__(self, alpha_heuristica: float = 1.5):
        """
        Args:
            alpha_heuristica: Fator de ajuste para a heurística do robô.
                             > 1.0 = acredita que o robô melhora a probabilidade
                             = 1.0 = usa probabilidade implícita do mercado
                             < 1.0 = mais conservador
        """
        self.alpha_heuristica = alpha_heuristica
    
    def estimar_probabilidade(self, trava: TravaOperation) -> float:
        """
        Estima a probabilidade de sucesso de uma trava.
        
        Baseado na discussão do ideia.md:
        - Payoff alto (1000%+) geralmente implica probabilidade baixa (10-15% mercado)
        - Distância do ativo maior = probabilidade menor
        - O robô pode melhorar a probabilidade (alpha_heuristica)
        
        Fórmula heurística melhorada:
        - Probabilidade base = função do payoff (mercado eficiente)
        - Ajuste pela distância (quanto maior, menor a prob)
        - Aplicação do alpha_heuristica (robô melhora a prob)
        """
        """
        Estima probabilidade usando distância como fator principal.
        
        Baseado na discussão: distância maior = probabilidade menor.
        Payoff alto indica que mercado precifica como baixa probabilidade,
        mas o robô pode melhorar isso.
        """
        # Probabilidade baseada na distância do ativo
        # Distância menor = probabilidade maior
        # Distância de 6% → prob base ~18-20%
        # Distância de 10% → prob base ~12-15%
        # Distância de 15% → prob base ~8-10%
        # Fórmula: prob_base = 25 - (distância * 1.2)
        prob_base_distancia = 25.0 - (trava.distancia_ativo * 1.2)
        prob_base_distancia = max(8.0, min(22.0, prob_base_distancia))
        
        # Ajuste pelo payoff (payoff muito alto reduz prob)
        # Payoff 2400% → reduz prob em ~20%
        # Payoff 1500% → reduz prob em ~10%
        # Payoff 1000% → não reduz
        if trava.payoff > 2000:
            fator_payoff = 0.8  # Reduz 20%
        elif trava.payoff > 1500:
            fator_payoff = 0.9  # Reduz 10%
        else:
            fator_payoff = 1.0  # Não reduz
        
        prob_ajustada = prob_base_distancia * fator_payoff
        
        # Aplica alpha_heuristica (se o robô é bom, aumenta a prob)
        # Alpha 1.5 = acredita que robô melhora prob em 50%
        prob_final = prob_ajustada * self.alpha_heuristica
        
        # Limites razoáveis: entre 10% e 30%
        # Mínimo de 10% (mais realista para travas OTM com heurística)
        # Máximo de 30% (não exagerar - travas OTM raramente têm >30%)
        prob_final = max(10.0, min(30.0, prob_final))
        
        return prob_final
    
    def calcular_esperanca_estatistica(self, trava: TravaOperation) -> float:
        """
        Calcula a esperança estatística (Expected Value) de uma trava.
        
        EV = (Probabilidade × Retorno_Positivo) + ((1 - Probabilidade) × Retorno_Negativo)
        
        Para travas:
        - Retorno Positivo = Payoff (%)
        - Retorno Negativo = -100% (perde tudo)
        """
        prob = self.estimar_probabilidade(trava) / 100.0  # Converte para decimal
        retorno_positivo = trava.payoff / 100.0  # Converte para decimal (ex: 2400% = 24.0)
        retorno_negativo = -1.0  # Perde 100% do investimento
        
        ev = (prob * retorno_positivo) + ((1 - prob) * retorno_negativo)
        
        return ev * 100.0  # Retorna em %
    
    def calcular_alocacoes(
        self,
        travas: List[TravaOperation],
        capital_total: float,
        metodo: str = "proporcional"
    ) -> List[AlocacaoTrava]:
        """
        Calcula alocações de capital para uma lista de travas.
        
        Args:
            travas: Lista de travas
            capital_total: Capital total disponível para investir
            metodo: Método de alocação
                - "proporcional": Proporcional à esperança estatística
                - "kelly": Critério de Kelly (mais agressivo)
                - "equal_risk": Alocação igual por risco (custo)
        
        Returns:
            Lista de AlocacaoTrava ordenada por esperança estatística (maior primeiro)
        """
        alocacoes = []
        
        # Calcula esperança estatística para cada trava
        for trava in travas:
            prob = self.estimar_probabilidade(trava)
            ev = self.calcular_esperanca_estatistica(trava)
            
            alocacoes.append(AlocacaoTrava(
                trava=trava,
                probabilidade_estimada=prob,
                esperanca_estatistica=ev,
                alocacao_pct=0.0,  # Será calculado depois
                alocacao_valor=0.0,  # Será calculado depois
                retorno_esperado=0.0  # Será calculado depois
            ))
        
        # Ordena por esperança estatística (maior primeiro)
        alocacoes.sort(key=lambda x: x.esperanca_estatistica, reverse=True)
        
        # Calcula alocações baseado no método escolhido
        if metodo == "proporcional":
            self._alocar_proporcional(alocacoes, capital_total)
        elif metodo == "kelly":
            self._alocar_kelly(alocacoes, capital_total)
        elif metodo == "equal_risk":
            self._alocar_equal_risk(alocacoes, capital_total)
        else:
            raise ValueError(f"Método desconhecido: {metodo}")
        
        return alocacoes
    
    def _alocar_proporcional(self, alocacoes: List[AlocacaoTrava], capital_total: float):
        """
        Aloca capital proporcionalmente à esperança estatística.
        
        Travas com maior EV recebem mais capital.
        """
        # Filtra apenas travas com EV positivo
        travas_positivas = [a for a in alocacoes if a.esperanca_estatistica > 0]
        
        if not travas_positivas:
            # Se nenhuma tem EV positivo, não aloca nada
            return
        
        # Soma das esperanças estatísticas positivas
        soma_ev = sum(a.esperanca_estatistica for a in travas_positivas)
        
        if soma_ev == 0:
            return
        
        # Aloca proporcionalmente
        for aloc in travas_positivas:
            if aloc.esperanca_estatistica > 0:
                aloc.alocacao_pct = (aloc.esperanca_estatistica / soma_ev) * 100.0
                aloc.alocacao_valor = (capital_total * aloc.alocacao_pct) / 100.0
                aloc.retorno_esperado = aloc.alocacao_valor * (aloc.esperanca_estatistica / 100.0)
    
    def _alocar_kelly(self, alocacoes: List[AlocacaoTrava], capital_total: float):
        """
        Aloca usando Critério de Kelly simplificado.
        
        Kelly = (Prob × Retorno - (1 - Prob)) / Retorno
        """
        for aloc in alocacoes:
            if aloc.esperanca_estatistica > 0:
                prob = aloc.probabilidade_estimada / 100.0
                retorno = aloc.trava.payoff / 100.0
                
                # Critério de Kelly
                kelly = (prob * retorno - (1 - prob)) / retorno
                kelly = max(0, min(kelly, 0.25))  # Limita a 25% por operação
                
                aloc.alocacao_pct = kelly * 100.0
                aloc.alocacao_valor = capital_total * kelly
                aloc.retorno_esperado = aloc.alocacao_valor * (aloc.esperanca_estatistica / 100.0)
    
    def _alocar_equal_risk(self, alocacoes: List[AlocacaoTrava], capital_total: float):
        """
        Aloca igualmente por risco (custo total).
        
        Cada trava recebe o mesmo valor em risco.
        """
        travas_positivas = [a for a in alocacoes if a.esperanca_estatistica > 0]
        
        if not travas_positivas:
            return
        
        # Aloca igualmente
        valor_por_trava = capital_total / len(travas_positivas)
        
        for aloc in travas_positivas:
            aloc.alocacao_valor = valor_por_trava
            aloc.alocacao_pct = (valor_por_trava / capital_total) * 100.0
            aloc.retorno_esperado = aloc.alocacao_valor * (aloc.esperanca_estatistica / 100.0)


def calcular_alocacao_travas(
    travas: List[TravaOperation],
    capital_total: float,
    alpha_heuristica: float = 1.5,
    metodo: str = "proporcional"
) -> List[AlocacaoTrava]:
    """
    Função helper para calcular alocações de travas.
    
    Args:
        travas: Lista de travas
        capital_total: Capital total disponível
        alpha_heuristica: Fator de ajuste (1.5 = acredita que robô melhora prob em 50%)
        metodo: Método de alocação (proporcional, kelly, equal_risk)
    
    Returns:
        Lista de alocações ordenada por esperança estatística
    """
    calculadora = EsperancaEstatistica(alpha_heuristica=alpha_heuristica)
    return calculadora.calcular_alocacoes(travas, capital_total, metodo)

