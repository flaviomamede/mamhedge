"""
Sistema de cálculo de Esperança Estatística e alocação de capital para TERFs.

Baseado na discussão do ideia.md:
- TERFs têm alta probabilidade de sucesso (75-98%)
- Retorno positivo: rentabilidade_miolo (metade do potencial, ~2.5% se potencial é 5%)
- Retorno negativo: perda limitada (no máximo um período de CDI, ou perda se ação cair muito)
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from ..data.parsers.everhedge_parser import TERFOperation


@dataclass
class AlocacaoTERF:
    """Alocação calculada para uma TERF."""
    terf: TERFOperation
    probabilidade_estimada: float  # Probabilidade estimada de sucesso (%)
    retorno_esperado_positivo: float  # Retorno esperado se der certo (%)
    retorno_esperado_negativo: float  # Retorno esperado se der errado (%)
    esperanca_estatistica: float  # Esperança estatística (EV)
    alocacao_pct: float  # Porcentagem do capital total a alocar
    alocacao_valor: float  # Valor em R$ a alocar
    retorno_esperado: float  # Retorno esperado em R$


class EsperancaTERF:
    """
    Calcula esperança estatística e aloca capital entre TERFs.
    
    Baseado na discussão do ideia.md:
    - Probabilidade: 75-98% (dependendo do manejo e rating)
    - Retorno positivo: metade do potencial (2.5% se potencial é 5%)
    - Retorno negativo: perda limitada (0% a -1% do CDI, ou perda se ação cair muito)
    """
    
    def __init__(self, alpha_heuristica: float = 1.0):
        """
        Args:
            alpha_heuristica: Fator de ajuste para a heurística.
                             Para TERFs, geralmente próximo de 1.0 (já são conservadoras)
        """
        self.alpha_heuristica = alpha_heuristica
    
    def estimar_probabilidade(self, terf: TERFOperation) -> float:
        """
        Estima a probabilidade de sucesso de uma TERF.
        
        Baseado na discussão:
        - Rating *** (Excelente): ~98% de probabilidade
        - Rating ** (Muito Boa): ~90% de probabilidade
        - Rating * (Boa): ~80% de probabilidade
        - Sem rating: ~75% de probabilidade (padrão dos apps)
        
        Aplicativos mostram 75-80%, mas com manejo adequado pode chegar a 98%.
        """
        # Probabilidade base no rating
        if terf.rating == "***":
            prob_base = 98.0
        elif terf.rating == "**":
            prob_base = 90.0
        elif terf.rating == "*":
            prob_base = 80.0
        else:
            prob_base = 75.0  # Padrão dos aplicativos
        
        # Ajuste pela rentabilidade (rentabilidade maior = mais confiança)
        # Rentabilidade miolo > 3% = aumenta prob em 2%
        # Rentabilidade miolo < 2% = reduz prob em 2%
        if terf.rentabilidade_miolo > 3.0:
            prob_ajustada = prob_base + 2.0
        elif terf.rentabilidade_miolo < 2.0:
            prob_ajustada = prob_base - 2.0
        else:
            prob_ajustada = prob_base
        
        # Aplica alpha_heuristica
        prob_final = prob_ajustada * self.alpha_heuristica
        
        # Limites: entre 70% e 99%
        prob_final = max(70.0, min(99.0, prob_final))
        
        return prob_final
    
    def estimar_retornos(self, terf: TERFOperation) -> tuple[float, float]:
        """
        Estima retorno positivo e negativo de uma TERF.
        
        Retorna: (retorno_positivo, retorno_negativo) em %
        
        Baseado na discussão:
        - Retorno positivo: metade do potencial (2.5% se potencial é 5%)
        - Retorno negativo: perda limitada (0% a -1% do CDI, ou perda se ação cair muito)
        """
        # Retorno positivo: metade do potencial (rentabilidade_miolo)
        # Mas usa rentabilidade_miolo como base (já é o retorno esperado)
        retorno_positivo = terf.rentabilidade_miolo * 0.5  # Metade do potencial
        
        # Retorno negativo: perda limitada
        # Segundo a discussão: "perde no máximo um período de CDI"
        # Ou pode ter perda se ação cair muito (mas é limitada pelo strike da PUT)
        # Estimativa conservadora: -0.5% a -1% do CDI
        # Usa CDI do período como referência
        retorno_negativo = -terf.cdi_periodo * 0.5  # Metade do CDI como perda máxima
        
        # Limita perda máxima a -2% (muito conservador)
        retorno_negativo = max(-2.0, retorno_negativo)
        
        return (retorno_positivo, retorno_negativo)
    
    def calcular_esperanca_estatistica(self, terf: TERFOperation) -> float:
        """
        Calcula a esperança estatística (Expected Value) de uma TERF.
        
        EV = (Probabilidade × Retorno_Positivo) + ((1 - Probabilidade) × Retorno_Negativo)
        """
        prob = self.estimar_probabilidade(terf) / 100.0
        retorno_pos, retorno_neg = self.estimar_retornos(terf)
        
        ev = (prob * retorno_pos) + ((1 - prob) * retorno_neg)
        
        return ev
    
    def calcular_alocacoes(
        self,
        terfs: List[TERFOperation],
        capital_total: float,
        metodo: str = "proporcional"
    ) -> List[AlocacaoTERF]:
        """
        Calcula alocações de capital para uma lista de TERFs.
        
        Args:
            terfs: Lista de TERFs
            capital_total: Capital total disponível para investir
            metodo: Método de alocação
                - "proporcional": Proporcional à esperança estatística
                - "equal_risk": Alocação igual por risco (coeficiente)
        
        Returns:
            Lista de AlocacaoTERF ordenada por esperança estatística (maior primeiro)
        """
        alocacoes = []
        
        # Calcula esperança estatística para cada TERF
        for terf in terfs:
            prob = self.estimar_probabilidade(terf)
            retorno_pos, retorno_neg = self.estimar_retornos(terf)
            ev = self.calcular_esperanca_estatistica(terf)
            
            alocacoes.append(AlocacaoTERF(
                terf=terf,
                probabilidade_estimada=prob,
                retorno_esperado_positivo=retorno_pos,
                retorno_esperado_negativo=retorno_neg,
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
        elif metodo == "equal_risk":
            self._alocar_equal_risk(alocacoes, capital_total)
        else:
            raise ValueError(f"Método desconhecido: {metodo}")
        
        return alocacoes
    
    def _alocar_proporcional(self, alocacoes: List[AlocacaoTERF], capital_total: float):
        """Aloca capital proporcionalmente à esperança estatística."""
        # Filtra apenas TERFs com EV positivo
        terfs_positivas = [a for a in alocacoes if a.esperanca_estatistica > 0]
        
        if not terfs_positivas:
            return
        
        # Soma das esperanças estatísticas positivas
        soma_ev = sum(a.esperanca_estatistica for a in terfs_positivas)
        
        if soma_ev == 0:
            return
        
        # Aloca proporcionalmente
        for aloc in terfs_positivas:
            if aloc.esperanca_estatistica > 0:
                aloc.alocacao_pct = (aloc.esperanca_estatistica / soma_ev) * 100.0
                aloc.alocacao_valor = (capital_total * aloc.alocacao_pct) / 100.0
                aloc.retorno_esperado = aloc.alocacao_valor * (aloc.esperanca_estatistica / 100.0)
    
    def _alocar_equal_risk(self, alocacoes: List[AlocacaoTERF], capital_total: float):
        """Aloca igualmente por risco (coeficiente)."""
        terfs_positivas = [a for a in alocacoes if a.esperanca_estatistica > 0]
        
        if not terfs_positivas:
            return
        
        # Aloca igualmente
        valor_por_terf = capital_total / len(terfs_positivas)
        
        for aloc in terfs_positivas:
            aloc.alocacao_valor = valor_por_terf
            aloc.alocacao_pct = (valor_por_terf / capital_total) * 100.0
            aloc.retorno_esperado = aloc.alocacao_valor * (aloc.esperanca_estatistica / 100.0)


def calcular_alocacao_terfs(
    terfs: List[TERFOperation],
    capital_total: float,
    alpha_heuristica: float = 1.0,
    metodo: str = "proporcional"
) -> List[AlocacaoTERF]:
    """
    Função helper para calcular alocações de TERFs.
    
    Args:
        terfs: Lista de TERFs
        capital_total: Capital total disponível
        alpha_heuristica: Fator de ajuste (1.0 = padrão para TERFs)
        metodo: Método de alocação (proporcional, equal_risk)
    
    Returns:
        Lista de alocações ordenada por esperança estatística
    """
    calculadora = EsperancaTERF(alpha_heuristica=alpha_heuristica)
    return calculadora.calcular_alocacoes(terfs, capital_total, metodo)

