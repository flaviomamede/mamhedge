"""
Parser para processar dados de travas (spreads) do robô da EverHedge.

Formato das travas:
- Ação, Preço, Data
- C: (opção comprada) - Strike, Valor
- V: (opção vendida) - Strike, Valor
- Distância do ativo, Custo Total, Payoff
"""

import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class TravaOperation:
    """Estrutura de dados para uma operação de trava sugerida pelo robô."""
    
    # Informações da Ação
    acao: str  # Código da ação (ex: PETR4)
    preco_acao: float  # Preço de referência da ação
    data_busca: datetime  # Data de busca da trava
    
    # Opção Comprada (C)
    codigo_comprada: str  # Código da opção comprada (ex: PETRN311)
    strike_comprada: float  # Strike da opção comprada
    valor_comprada: float  # Valor negociado da opção comprada
    
    # Opção Vendida (V)
    codigo_vendida: str  # Código da opção vendida (ex: PETRN306)
    strike_vendida: float  # Strike da opção vendida
    valor_vendida: float  # Valor negociado da opção vendida
    
    # Informações da Estrutura
    distancia_ativo: float  # Distância do ativo com o primeiro strike (%)
    custo_total: float  # Custo total da trava
    payoff: float  # Payoff máximo da operação (%)
    
    # Tipo de trava (inferido)
    tipo_trava: str = "Baixa"  # "Baixa" (Bear Put Spread) ou "Alta" (Bull Call Spread)


class TravaParser:
    """Parser para processar texto copiado do robô da EverHedge com travas."""
    
    def __init__(self):
        # Padrões regex para extrair informações
        self.patterns = {
            'acao': re.compile(r'Ação:\s*([A-Z0-9]+)', re.IGNORECASE),
            'preco': re.compile(r'Preço:\s*R\$\s*([\d,]+)', re.IGNORECASE),
            'data': re.compile(r'Data:\s*(\d{2}/\d{2}/\d{4})'),
            'comprada_codigo': re.compile(r'C:\s*([A-Z0-9]+)', re.IGNORECASE),
            'comprada_strike': re.compile(r'Strike:\s*R\$\s*([\d,]+)', re.IGNORECASE),
            'comprada_valor': re.compile(r'Valor:\s*R\$\s*([\d,]+)', re.IGNORECASE),
            'vendida_codigo': re.compile(r'V:\s*([A-Z0-9]+)', re.IGNORECASE),
            'distancia': re.compile(r'Distância\s+do\s+ativo:\s*([\d,]+)%', re.IGNORECASE),
            'custo_total': re.compile(r'Custo\s+Total:\s*R\$\s*([\d,]+)', re.IGNORECASE),
            'payoff': re.compile(r'Payoff:\s*([\d.,]+)%', re.IGNORECASE),  # Aceita ponto e vírgula
        }
    
    def _parse_float(self, value: str) -> float:
        """
        Converte string brasileira para float.
        Formato: "2.400,00" ou "2400,00" ou "2400.00"
        """
        # Remove espaços
        value = value.strip()
        
        # Se tem ponto e vírgula, é formato brasileiro: "2.400,00"
        if '.' in value and ',' in value:
            # Remove pontos (milhares) e substitui vírgula por ponto (decimal)
            return float(value.replace('.', '').replace(',', '.'))
        # Se só tem vírgula, substitui por ponto
        elif ',' in value:
            return float(value.replace(',', '.'))
        # Se só tem ponto, pode ser decimal ou milhar
        elif '.' in value:
            # Se tem mais de 2 dígitos após o ponto, provavelmente é milhar
            parts = value.split('.')
            if len(parts) == 2 and len(parts[1]) > 2:
                # É milhar, remove o ponto
                return float(value.replace('.', ''))
            else:
                # É decimal
                return float(value)
        else:
            return float(value)
    
    def _parse_date(self, date_str: str) -> datetime:
        """Converte string de data DD/MM/YYYY para datetime."""
        return datetime.strptime(date_str, '%d/%m/%Y')
    
    def _extract_strikes_e_valores(self, text: str, start_pos: int) -> tuple[float, float, float, float]:
        """
        Extrai strikes e valores das opções comprada e vendida.
        
        Formato esperado:
        C:CODIGO
        Strike:R$ X,XX
        Valor:R$ X,XX
        V:CODIGO
        Strike:R$ X,XX
        Valor:R$ X,XX
        
        Retorna: (strike_comprada, valor_comprada, strike_vendida, valor_vendida)
        """
        lines = text.split('\n')
        
        strike_comprada = None
        valor_comprada = None
        strike_vendida = None
        valor_vendida = None
        
        # Procura por "C:" e depois "V:"
        encontrou_c = False
        encontrou_v = False
        
        for i, line in enumerate(lines):
            if i < start_pos:
                continue
            
            # Procura opção comprada (C:)
            if not encontrou_c and re.match(r'C:\s*[A-Z0-9]+', line, re.IGNORECASE):
                encontrou_c = True
                # Próxima linha deve ter Strike
                if i + 1 < len(lines):
                    strike_match = self.patterns['comprada_strike'].search(lines[i + 1])
                    if strike_match:
                        strike_comprada = self._parse_float(strike_match.group(1))
                # Linha seguinte deve ter Valor
                if i + 2 < len(lines):
                    valor_match = self.patterns['comprada_valor'].search(lines[i + 2])
                    if valor_match:
                        valor_comprada = self._parse_float(valor_match.group(1))
            
            # Procura opção vendida (V:)
            if not encontrou_v and re.match(r'V:\s*[A-Z0-9]+', line, re.IGNORECASE):
                encontrou_v = True
                # Próxima linha deve ter Strike
                if i + 1 < len(lines):
                    strike_match = self.patterns['comprada_strike'].search(lines[i + 1])
                    if strike_match:
                        strike_vendida = self._parse_float(strike_match.group(1))
                # Linha seguinte deve ter Valor
                if i + 2 < len(lines):
                    valor_match = self.patterns['comprada_valor'].search(lines[i + 2])
                    if valor_match:
                        valor_vendida = self._parse_float(valor_match.group(1))
            
            if encontrou_c and encontrou_v:
                break
        
        return (strike_comprada or 0.0, valor_comprada or 0.0, strike_vendida or 0.0, valor_vendida or 0.0)
    
    def parse_operation(self, text: str, start_line: int = 0) -> Optional[TravaOperation]:
        """
        Parse uma operação de trava do texto.
        
        Args:
            text: Texto completo copiado do robô
            start_line: Linha inicial para começar a busca
        
        Returns:
            TravaOperation ou None se não conseguir parsear
        """
        lines = text.split('\n')
        
        # Encontra o fim desta operação (próxima "Ação:" ou fim do arquivo)
        end_line = len(lines)
        for i in range(start_line + 1, len(lines)):
            if re.match(r'Ação:\s*[A-Z0-9]+', lines[i], re.IGNORECASE):
                end_line = i
                break
        
        # Cria seção de texto apenas desta operação
        text_section = '\n'.join(lines[start_line:end_line])
        
        # Extrai informações básicas
        acao_match = self.patterns['acao'].search(text_section)
        if not acao_match:
            return None
        
        acao = acao_match.group(1)
        
        # Extrai preço
        preco_match = self.patterns['preco'].search(text_section)
        if not preco_match:
            return None
        preco_acao = self._parse_float(preco_match.group(1))
        
        # Extrai data
        data_match = self.patterns['data'].search(text_section)
        if not data_match:
            return None
        data_busca = self._parse_date(data_match.group(1))
        
        # Extrai opção comprada
        comprada_codigo_match = self.patterns['comprada_codigo'].search(text_section)
        if not comprada_codigo_match:
            return None
        codigo_comprada = comprada_codigo_match.group(1)
        
        # Extrai opção vendida
        vendida_codigo_match = self.patterns['vendida_codigo'].search(text_section)
        if not vendida_codigo_match:
            return None
        codigo_vendida = vendida_codigo_match.group(1)
        
        # Extrai strikes e valores
        strike_comp, valor_comp, strike_vend, valor_vend = self._extract_strikes_e_valores(text, start_line)
        
        if strike_comp == 0 or valor_comp == 0 or strike_vend == 0 or valor_vend == 0:
            return None
        
        # Extrai distância do ativo
        distancia_match = self.patterns['distancia'].search(text_section)
        distancia_ativo = self._parse_float(distancia_match.group(1)) if distancia_match else 0.0
        
        # Extrai custo total
        custo_match = self.patterns['custo_total'].search(text_section)
        if not custo_match:
            return None
        custo_total = self._parse_float(custo_match.group(1))
        
        # Extrai payoff
        payoff_match = self.patterns['payoff'].search(text_section)
        if not payoff_match:
            return None
        payoff = self._parse_float(payoff_match.group(1))
        
        # Determina tipo de trava (se strikes são menores que preço da ação, é trava de baixa)
        tipo_trava = "Baixa" if strike_comp < preco_acao else "Alta"
        
        return TravaOperation(
            acao=acao,
            preco_acao=preco_acao,
            data_busca=data_busca,
            codigo_comprada=codigo_comprada,
            strike_comprada=strike_comp,
            valor_comprada=valor_comp,
            codigo_vendida=codigo_vendida,
            strike_vendida=strike_vend,
            valor_vendida=valor_vend,
            distancia_ativo=distancia_ativo,
            custo_total=custo_total,
            payoff=payoff,
            tipo_trava=tipo_trava
        )
    
    def parse_all_operations(self, text: str) -> List[TravaOperation]:
        """
        Parse todas as operações de trava presentes no texto.
        
        Args:
            text: Texto completo copiado do robô
        
        Returns:
            Lista de TravaOperation
        """
        operations = []
        lines = text.split('\n')
        
        # Encontra todas as ocorrências de "Ação:" que marcam início de operação
        operation_starts = []
        for i, line in enumerate(lines):
            if re.match(r'Ação:\s*[A-Z0-9]+', line, re.IGNORECASE):
                # Verifica se é uma trava (tem C: e V: nas próximas linhas)
                for j in range(i, min(i + 15, len(lines))):
                    if re.match(r'C:\s*[A-Z0-9]+', lines[j], re.IGNORECASE):
                        operation_starts.append(i)
                        break
        
        # Parse cada operação
        for start_line in operation_starts:
            operation = self.parse_operation(text, start_line)
            if operation:
                operations.append(operation)
        
        return operations
    
    def to_dict(self, operation: TravaOperation) -> Dict:
        """Converte uma TravaOperation para dicionário."""
        return {
            'acao': operation.acao,
            'preco_acao': operation.preco_acao,
            'data_busca': operation.data_busca.isoformat(),
            'codigo_comprada': operation.codigo_comprada,
            'strike_comprada': operation.strike_comprada,
            'valor_comprada': operation.valor_comprada,
            'codigo_vendida': operation.codigo_vendida,
            'strike_vendida': operation.strike_vendida,
            'valor_vendida': operation.valor_vendida,
            'distancia_ativo': operation.distancia_ativo,
            'custo_total': operation.custo_total,
            'payoff': operation.payoff,
            'tipo_trava': operation.tipo_trava
        }


if __name__ == "__main__":
    # Teste do parser
    import os
    
    radar_path = os.path.join(os.path.dirname(__file__), '../../../radar.md')
    
    if not os.path.exists(radar_path):
        print(f"Arquivo não encontrado: {radar_path}")
        exit(1)
    
    with open(radar_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    parser = TravaParser()
    operations = parser.parse_all_operations(text)
    
    print(f"Encontradas {len(operations)} operações de TRAVA\n")
    
    for i, op in enumerate(operations, 1):
        print(f"=== Trava {i} ===")
        print(f"Ação: {op.acao} @ R$ {op.preco_acao:.2f}")
        print(f"Data: {op.data_busca.strftime('%d/%m/%Y')}")
        print(f"Comprada: {op.codigo_comprada} - Strike R$ {op.strike_comprada:.2f} - Valor: R$ {op.valor_comprada:.2f}")
        print(f"Vendida: {op.codigo_vendida} - Strike R$ {op.strike_vendida:.2f} - Valor: R$ {op.valor_vendida:.2f}")
        print(f"Distância: {op.distancia_ativo:.2f}%")
        print(f"Custo Total: R$ {op.custo_total:.2f}")
        print(f"Payoff: {op.payoff:.2f}%")
        print(f"Tipo: Trava de {op.tipo_trava}")
        print()

