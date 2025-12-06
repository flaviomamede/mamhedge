"""
Parser para processar dados do robô da EverHedge copiados em formato texto.

O robô fornece sugestões de operações TERF (Travas Estruturadas de Retorno Flexível)
com todas as informações necessárias para análise e execução.
"""

import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class TERFOperation:
    """Estrutura de dados para uma operação TERF sugerida pelo robô."""
    
    # Informações da Ação
    acao: str  # Código da ação (ex: ITUB4)
    preco_acao: float  # Preço da ação negociada
    data_busca: datetime  # Data de busca do radar
    
    # Informações da Call (Vendida)
    codigo_call: str  # Código da Call (ex: ITUBA434)
    strike_call: float  # Strike da Call
    vencimento_call: datetime  # Data de vencimento da Call
    valor_call: float  # Valor negociado da Call
    
    # Informações da Put (Comprada)
    codigo_put: str  # Código da Put (ex: ITUBX43)
    strike_put: float  # Strike da Put
    vencimento_put: datetime  # Data de vencimento da Put
    valor_put: float  # Valor negociado da Put
    
    # Informações da Estrutura
    coeficiente: float  # Coeficiente total (Ação + Put - Call)
    rentabilidade_miolo: float  # Rentabilidade do miolo no vencimento da opção curta
    rentabilidade_cima: float  # Rentabilidade para cima até vencimento da opção longa
    rentabilidade_baixo: float  # Rentabilidade para baixo até vencimento da opção longa
    meses: int  # Número de meses até vencimento da Put
    cdi_periodo: float  # CDI do período até vencimento da Put (%)
    rating: str  # Classificação: * (Boa), ** (Muito Boa), *** (Excelente)
    tipo: str  # Tipo da operação (ex: U)
    
    # Metadados
    operacao: str = "V"  # V = Vender, C = Comprar (para Call)
    operacao_put: str = "C"  # C = Comprar (para Put)
    
    def to_dict(self) -> Dict:
        """Converte uma TERFOperation para dicionário."""
        return {
            'acao': self.acao,
            'preco_acao': self.preco_acao,
            'data_busca': self.data_busca.isoformat(),
            'codigo_call': self.codigo_call,
            'strike_call': self.strike_call,
            'vencimento_call': self.vencimento_call.isoformat(),
            'valor_call': self.valor_call,
            'codigo_put': self.codigo_put,
            'strike_put': self.strike_put,
            'vencimento_put': self.vencimento_put.isoformat(),
            'valor_put': self.valor_put,
            'coeficiente': self.coeficiente,
            'rentabilidade_miolo': self.rentabilidade_miolo,
            'rentabilidade_cima': self.rentabilidade_cima,
            'rentabilidade_baixo': self.rentabilidade_baixo,
            'meses': self.meses,
            'cdi_periodo': self.cdi_periodo,
            'rating': self.rating,
            'tipo': self.tipo,
            'operacao': self.operacao,
            'operacao_put': self.operacao_put
        }


class EverHedgeParser:
    """Parser para processar texto copiado do robô da EverHedge."""
    
    def __init__(self):
        # Padrões regex para extrair informações
        # Nota: Aceita formatos com ou sem espaços após ":"
        self.patterns = {
            'acao': re.compile(r'[CV]\s*Ação:\s*([A-Z0-9]+)', re.IGNORECASE),
            'preco': re.compile(r'Preço:\s*R\$\s*([\d,]+)', re.IGNORECASE),
            'data': re.compile(r'Data:\s*(\d{2}/\d{2}/\d{4})'),
            'call_codigo': re.compile(r'[CV]\s*Call:\s*([A-Z0-9]+)', re.IGNORECASE),
            'call_strike': re.compile(r'Strike\s*Call:\s*R\$\s*:?\s*([\d,]+)', re.IGNORECASE),  # Aceita "R$:" ou "R$"
            'call_venc': re.compile(r'Venc\.\s*Call:\s*(\d{2}/\d{2}/\d{4})', re.IGNORECASE),
            'put_codigo': re.compile(r'[CV]\s*Put:\s*([A-Z0-9]+)', re.IGNORECASE),
            'put_strike': re.compile(r'Strike\s*Put:\s*R\$\s*([\d,]+)', re.IGNORECASE),
            'put_venc': re.compile(r'Venc\.\s*Put:\s*(\d{2}/\d{2}/\d{4})', re.IGNORECASE),
            'coeficiente': re.compile(r'Coeficiente:\s*R\$\s*([\d,]+)', re.IGNORECASE),
            'meses': re.compile(r'Meses:\s*(\d+)', re.IGNORECASE),
            'cdi': re.compile(r'CDI\s*Período:\s*([\d,]+)%', re.IGNORECASE),
            'rating': re.compile(r'Rating:\s*(\*+)', re.IGNORECASE),
            'tipo': re.compile(r'Tipo:\s*([A-Z])', re.IGNORECASE),
        }
    
    def _parse_float(self, value: str) -> float:
        """Converte string brasileira (com vírgula) para float."""
        return float(value.replace(',', '.'))
    
    def _parse_date(self, date_str: str) -> datetime:
        """Converte string de data DD/MM/YYYY para datetime."""
        return datetime.strptime(date_str, '%d/%m/%Y')
    
    def _extract_rentabilidade(self, text: str, start_pos: int) -> tuple[float, float, float]:
        """
        Extrai os três valores de rentabilidade após a linha 'Rentabilidade:'.
        
        Retorna: (miolo, cima, baixo)
        """
        lines = text.split('\n')
        rent_values = []
        
        # Procura a linha "Rentabilidade:" e pega as 3 linhas seguintes
        for i, line in enumerate(lines):
            if i < start_pos:
                continue
            # Verifica se a linha contém "Rentabilidade:" (case insensitive)
            line_lower = line.lower().strip()
            if 'rentabilidade:' in line_lower:
                # Pega as próximas 3 linhas que contêm números com %
                for j in range(i + 1, min(i + 4, len(lines))):
                    line_clean = lines[j].strip()
                    # Aceita formato "0,35%" ou "0.35%" - busca qualquer número com vírgula/ponto e %
                    if line_clean:
                        # Busca padrão: dígitos, vírgula ou ponto, mais dígitos, seguido de %
                        # Usa search ao invés de findall para pegar o primeiro match
                        match = re.search(r'(\d+[,\.]\d+)%', line_clean)
                        if match:
                            value_str = match.group(1).replace(',', '.')
                            try:
                                rent_values.append(float(value_str))
                            except ValueError:
                                pass
                break
        
        if len(rent_values) >= 3:
            return (rent_values[0], rent_values[1], rent_values[2])
        elif len(rent_values) == 2:
            return (rent_values[0], rent_values[1], 0.0)
        elif len(rent_values) == 1:
            return (rent_values[0], 0.0, 0.0)
        return (0.0, 0.0, 0.0)
    
    def _extract_valor_call_put(self, text: str, start_pos: int) -> tuple[float, float]:
        """
        Extrai os valores da Call e da Put.
        
        O formato é:
        Valor: R$ X,XX  (valor da Call)
        C Put: ...
        ...
        Valor: R$ Y,YY  (valor da Put)
        """
        lines = text.split('\n')
        valores = []
        
        # Procura por linhas "Valor:" que contenham "R$"
        # O primeiro "Valor:" após a Call é o valor da Call
        # O segundo "Valor:" após a Put é o valor da Put
        for i, line in enumerate(lines):
            if i < start_pos:
                continue
            # Aceita "Valor:R$" ou "Valor: R$"
            if re.match(r'Valor:\s*R\$\s*[\d,]+', line, re.IGNORECASE):
                match = re.search(r'R\$\s*([\d,]+)', line)
                if match:
                    valores.append(self._parse_float(match.group(1)))
        
        if len(valores) >= 2:
            return (valores[0], valores[1])  # (call, put)
        elif len(valores) == 1:
            return (valores[0], 0.0)
        return (0.0, 0.0)
    
    def parse_operation(self, text: str, start_line: int = 0) -> Optional[TERFOperation]:
        """
        Parse uma operação TERF do texto.
        
        Args:
            text: Texto completo copiado do robô
            start_line: Linha inicial para começar a busca (para múltiplas operações)
        
        Returns:
            TERFOperation ou None se não conseguir parsear
        """
        lines = text.split('\n')
        
        # Encontra o fim desta operação (próxima "C Ação:" ou "V Ação:" ou fim do arquivo)
        end_line = len(lines)
        for i in range(start_line + 1, len(lines)):
            if re.match(r'[CV]\s*Ação:', lines[i], re.IGNORECASE):
                end_line = i
                break
        
        # Cria seção de texto apenas desta operação
        text_section = '\n'.join(lines[start_line:end_line])
        
        # Extrai informações básicas
        acao_match = self.patterns['acao'].search(text_section)
        if not acao_match:
            return None
        
        # Determina se é V (Vender) ou C (Comprar) para Call
        operacao_match = re.search(r'([CV])\s*Ação:', text_section)
        operacao = operacao_match.group(1) if operacao_match else "V"
        
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
        
        # Extrai Call
        call_codigo_match = self.patterns['call_codigo'].search(text_section)
        call_strike_match = self.patterns['call_strike'].search(text_section)
        call_venc_match = self.patterns['call_venc'].search(text_section)
        
        if not all([call_codigo_match, call_strike_match, call_venc_match]):
            return None
        
        codigo_call = call_codigo_match.group(1)
        strike_call = self._parse_float(call_strike_match.group(1))
        vencimento_call = self._parse_date(call_venc_match.group(1))
        
        # Extrai Put
        put_codigo_match = self.patterns['put_codigo'].search(text_section)
        put_strike_match = self.patterns['put_strike'].search(text_section)
        put_venc_match = self.patterns['put_venc'].search(text_section)
        
        if not all([put_codigo_match, put_strike_match, put_venc_match]):
            return None
        
        codigo_put = put_codigo_match.group(1)
        strike_put = self._parse_float(put_strike_match.group(1))
        vencimento_put = self._parse_date(put_venc_match.group(1))
        
        # Extrai valores (Call e Put) - agora dentro da seção
        valor_call, valor_put = self._extract_valor_call_put(text_section, 0)
        
        # Extrai coeficiente
        coeficiente_match = self.patterns['coeficiente'].search(text_section)
        if not coeficiente_match:
            return None
        coeficiente = self._parse_float(coeficiente_match.group(1))
        
        # Extrai rentabilidades - agora dentro da seção
        rent_miolo, rent_cima, rent_baixo = self._extract_rentabilidade(text_section, 0)
        
        # Extrai meses
        meses_match = self.patterns['meses'].search(text_section)
        meses = int(meses_match.group(1)) if meses_match else 0
        
        # Extrai CDI
        cdi_match = self.patterns['cdi'].search(text_section)
        cdi_periodo = self._parse_float(cdi_match.group(1)) if cdi_match else 0.0
        
        # Extrai rating
        rating_match = self.patterns['rating'].search(text_section)
        rating = rating_match.group(1) if rating_match else "*"
        
        # Extrai tipo
        tipo_match = self.patterns['tipo'].search(text_section)
        tipo = tipo_match.group(1) if tipo_match else "U"
        
        return TERFOperation(
            acao=acao,
            preco_acao=preco_acao,
            data_busca=data_busca,
            codigo_call=codigo_call,
            strike_call=strike_call,
            vencimento_call=vencimento_call,
            valor_call=valor_call,
            codigo_put=codigo_put,
            strike_put=strike_put,
            vencimento_put=vencimento_put,
            valor_put=valor_put,
            coeficiente=coeficiente,
            rentabilidade_miolo=rent_miolo,
            rentabilidade_cima=rent_cima,
            rentabilidade_baixo=rent_baixo,
            meses=meses,
            cdi_periodo=cdi_periodo,
            rating=rating,
            tipo=tipo,
            operacao=operacao
        )
    
    def parse_all_operations(self, text: str) -> List[TERFOperation]:
        """
        Parse todas as operações TERF presentes no texto.
        
        Args:
            text: Texto completo copiado do robô
        
        Returns:
            Lista de TERFOperation
        """
        operations = []
        lines = text.split('\n')
        
        # Encontra todas as ocorrências de "C Ação:" ou "V Ação:" que marcam início de operação
        operation_starts = []
        for i, line in enumerate(lines):
            if re.match(r'[CV]\s*Ação:', line, re.IGNORECASE):
                operation_starts.append(i)
        
        # Parse cada operação
        for start_line in operation_starts:
            operation = self.parse_operation(text, start_line)
            if operation:
                operations.append(operation)
        
        return operations
    
    def to_dict(self, operation: TERFOperation) -> Dict:
        """Converte uma TERFOperation para dicionário."""
        return {
            'acao': operation.acao,
            'preco_acao': operation.preco_acao,
            'data_busca': operation.data_busca.strftime('%d/%m/%Y'),
            'codigo_call': operation.codigo_call,
            'strike_call': operation.strike_call,
            'vencimento_call': operation.vencimento_call.strftime('%d/%m/%Y'),
            'valor_call': operation.valor_call,
            'codigo_put': operation.codigo_put,
            'strike_put': operation.strike_put,
            'vencimento_put': operation.vencimento_put.strftime('%d/%m/%Y'),
            'valor_put': operation.valor_put,
            'coeficiente': operation.coeficiente,
            'rentabilidade_miolo': operation.rentabilidade_miolo,
            'rentabilidade_cima': operation.rentabilidade_cima,
            'rentabilidade_baixo': operation.rentabilidade_baixo,
            'meses': operation.meses,
            'cdi_periodo': operation.cdi_periodo,
            'rating': operation.rating,
            'tipo': operation.tipo,
            'operacao': operation.operacao
        }


if __name__ == "__main__":
    # Teste do parser
    import os
    import sys
    
    # Ajusta o caminho relativo
    script_dir = os.path.dirname(os.path.abspath(__file__))
    radar_path = os.path.join(script_dir, '../../../radar.md')
    
    if not os.path.exists(radar_path):
        print(f"Arquivo não encontrado: {radar_path}")
        sys.exit(1)
    
    with open(radar_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    parser = EverHedgeParser()
    operations = parser.parse_all_operations(text)
    
    print(f"Encontradas {len(operations)} operações TERF\n")
    
    for i, op in enumerate(operations, 1):
        print(f"=== Operação {i} ===")
        print(f"Ação: {op.acao} @ R$ {op.preco_acao:.2f}")
        print(f"Data: {op.data_busca.strftime('%d/%m/%Y')}")
        print(f"Call: {op.codigo_call} - Strike R$ {op.strike_call:.2f} - Venc: {op.vencimento_call.strftime('%d/%m/%Y')} - Valor: R$ {op.valor_call:.2f}")
        print(f"Put: {op.codigo_put} - Strike R$ {op.strike_put:.2f} - Venc: {op.vencimento_put.strftime('%d/%m/%Y')} - Valor: R$ {op.valor_put:.2f}")
        print(f"Coeficiente: R$ {op.coeficiente:.2f}")
        print(f"Rentabilidade: Miolo {op.rentabilidade_miolo:.2f}% | Cima {op.rentabilidade_cima:.2f}% | Baixo {op.rentabilidade_baixo:.2f}%")
        print(f"Meses: {op.meses} | CDI Período: {op.cdi_periodo:.2f}%")
        print(f"Rating: {op.rating} | Tipo: {op.tipo}")
        print()

