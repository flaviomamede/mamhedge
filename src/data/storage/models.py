"""
Modelos de dados para operações registradas no sistema.

Expande a TERFOperation do parser para incluir informações de decisão,
consenso, e acompanhamento de resultados.
"""

from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
try:
    from ..parsers.everhedge_parser import TERFOperation
except ImportError:
    # Para testes isolados
    TERFOperation = None


class OperationStatus(Enum):
    """Status de uma operação no sistema."""
    SUGERIDA = "sugerida"  # Apenas parseada do robô, ainda não analisada
    ANALISADA = "analisada"  # Analisada mas não investida
    INVESTIDA_REAL = "investida_real"  # Investida em conta real
    INVESTIDA_SIMULADA = "investida_simulada"  # Investida em conta simulada
    ENCERRADA = "encerrada"  # Operação finalizada
    DESCARTADA = "descartada"  # Decisão de não investir


class AccountType(Enum):
    """Tipo de conta para execução."""
    REAL = "real"
    SIMULADA = "simulada"


class ConsensoLevel(Enum):
    """Nível de consenso dos relatórios."""
    FORTE = "forte"  # 3+ carteiras recomendam
    MEDIO = "medio"  # 1-2 carteiras recomendam
    NULO = "nulo"  # Nenhuma carteira menciona
    CONTRA = "contra"  # Carteiras recomendam venda/contra


class ConfiancaLevel(Enum):
    """Nível de confiança ajustada."""
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"


@dataclass
class RegisteredOperation:
    """
    Operação registrada no sistema com todas as informações de análise e decisão.
    
    Expande TERFOperation com campos de decisão, consenso e acompanhamento.
    """
    
    # ID único da operação
    id: Optional[str] = None  # UUID ou hash único
    
    # Dados originais do robô (TERFOperation)
    operacao_terf: Optional[TERFOperation] = None
    
    # Bloco 1: Filtro Bayesiano (Entrada)
    estrategia: str = "TERF"  # TERF, Trava Alta, Trava Baixa
    probabilidade_app: Optional[float] = None  # Probabilidade do app (Priori)
    consenso: Optional[ConsensoLevel] = None  # Nível de consenso dos relatórios
    confianca_ajustada: Optional[ConfiancaLevel] = None  # Confiança após análise bayesiana
    
    # Decisão de Investimento
    status: OperationStatus = OperationStatus.SUGERIDA
    conta_tipo: Optional[AccountType] = None  # Real ou Simulada
    data_decisao: Optional[datetime] = None  # Quando foi tomada a decisão
    motivo_decisao: Optional[str] = None  # Justificativa da decisão
    
    # Bloco 2: Execução e Monitoramento
    custo_montagem: Optional[float] = None  # Custo real de montagem
    alvo_saida: Optional[float] = None  # Alvo de saída em R$
    preco_atual: Optional[float] = None  # Preço atual no book
    resultado_atual_pct: Optional[float] = None  # Resultado atual em %
    distancia_alvo: Optional[float] = None  # Distância do alvo
    decisao_hoje: Optional[str] = None  # Decisão do dia (Segurar, Zerar, etc.)
    
    # Bloco 3: Validação (Posteriori)
    data_saida: Optional[datetime] = None
    lucro_prejuizo_real: Optional[float] = None  # Lucro/prejuízo em R$
    status_final: Optional[str] = None  # GAIN, LOSS, ou outro
    bayes_confirmou: Optional[bool] = None  # Se a análise bayesiana confirmou
    
    # Metadados
    data_registro: datetime = field(default_factory=datetime.now)
    data_atualizacao: datetime = field(default_factory=datetime.now)
    notas: Optional[str] = None  # Notas adicionais
    
    def to_dict(self) -> dict:
        """Converte para dicionário para armazenamento."""
        return {
            'id': self.id,
            'estrategia': self.estrategia,
            'probabilidade_app': self.probabilidade_app,
            'consenso': self.consenso.value if self.consenso else None,
            'confianca_ajustada': self.confianca_ajustada.value if self.confianca_ajustada else None,
            'status': self.status.value,
            'conta_tipo': self.conta_tipo.value if self.conta_tipo else None,
            'data_decisao': self.data_decisao.isoformat() if self.data_decisao else None,
            'motivo_decisao': self.motivo_decisao,
            'custo_montagem': self.custo_montagem,
            'alvo_saida': self.alvo_saida,
            'preco_atual': self.preco_atual,
            'resultado_atual_pct': self.resultado_atual_pct,
            'distancia_alvo': self.distancia_alvo,
            'decisao_hoje': self.decisao_hoje,
            'data_saida': self.data_saida.isoformat() if self.data_saida else None,
            'lucro_prejuizo_real': self.lucro_prejuizo_real,
            'status_final': self.status_final,
            'bayes_confirmou': self.bayes_confirmou,
            'data_registro': self.data_registro.isoformat(),
            'data_atualizacao': self.data_atualizacao.isoformat(),
            'notas': self.notas,
            # Dados da TERF
            'operacao_terf': self.operacao_terf.to_dict() if self.operacao_terf else None,
        }
    
    @classmethod
    def from_terf_operation(cls, terf_op: TERFOperation, id: Optional[str] = None) -> 'RegisteredOperation':
        """Cria uma RegisteredOperation a partir de uma TERFOperation."""
        import uuid
        return cls(
            id=id or str(uuid.uuid4()),
            operacao_terf=terf_op,
            estrategia="TERF",
            status=OperationStatus.SUGERIDA,
            data_registro=datetime.now(),
            data_atualizacao=datetime.now()
        )
    
    def marcar_investida(self, conta_tipo: AccountType, motivo: Optional[str] = None):
        """Marca a operação como investida (real ou simulada)."""
        self.status = OperationStatus.INVESTIDA_REAL if conta_tipo == AccountType.REAL else OperationStatus.INVESTIDA_SIMULADA
        self.conta_tipo = conta_tipo
        self.data_decisao = datetime.now()
        self.motivo_decisao = motivo
        self.data_atualizacao = datetime.now()
    
    def marcar_descartada(self, motivo: Optional[str] = None):
        """Marca a operação como descartada (não investida)."""
        self.status = OperationStatus.DESCARTADA
        self.data_decisao = datetime.now()
        self.motivo_decisao = motivo
        self.data_atualizacao = datetime.now()
    
    def encerrar(self, lucro_prejuizo: float, status_final: str, bayes_confirmou: Optional[bool] = None):
        """Encerra a operação com resultado final."""
        self.status = OperationStatus.ENCERRADA
        self.data_saida = datetime.now()
        self.lucro_prejuizo_real = lucro_prejuizo
        self.status_final = status_final
        self.bayes_confirmou = bayes_confirmou
        self.data_atualizacao = datetime.now()

