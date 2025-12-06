"""
Coletor de dados do site opcoes.net.br para atualizar preços de opções.

Permite consultar o preço atual de uma opção e calcular o rendimento.
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
from datetime import datetime
import re


class OpcoesNetCollector:
    """Coletor de dados do opcoes.net.br."""
    
    BASE_URL = "https://opcoes.net.br"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_option_data(self, codigo_opcao: str) -> Optional[Dict]:
        """
        Obtém dados de uma opção específica.
        
        Args:
            codigo_opcao: Código da opção (ex: PETRL311)
        
        Returns:
            Dicionário com dados da opção ou None se não encontrar
        """
        url = f"{self.BASE_URL}/{codigo_opcao}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrai informações da página
            data = {
                'codigo': codigo_opcao,
                'url': url,
                'data_consulta': datetime.now(),
            }
            
            # Tenta extrair preço atual (última cotação)
            # A página mostra uma tabela com os últimos 5 dias
            # Procura pela última linha da tabela
            
            # Procura por tabelas na página
            tables = soup.find_all('table')
            
            if tables:
                # Primeira tabela geralmente contém os dados principais
                first_table = tables[0]
                rows = first_table.find_all('tr')
                
                if len(rows) > 1:
                    # Segunda linha geralmente contém os dados mais recentes
                    latest_row = rows[1]
                    cells = latest_row.find_all('td')
                    
                    if len(cells) >= 4:
                        # Extrai preços (formato pode variar)
                        try:
                            # Tenta extrair o último preço (coluna "Ult")
                            ult_text = cells[3].get_text(strip=True)
                            # Remove pontos de milhar e converte vírgula para ponto
                            ult_clean = ult_text.replace('.', '').replace(',', '.')
                            data['preco_atual'] = float(ult_clean)
                        except (ValueError, IndexError):
                            pass
                        
                        try:
                            # Extrai preço médio
                            med_text = cells[2].get_text(strip=True)
                            med_clean = med_text.replace('.', '').replace(',', '.')
                            data['preco_medio'] = float(med_clean)
                        except (ValueError, IndexError):
                            pass
                        
                        try:
                            # Extrai preço mínimo
                            min_text = cells[0].get_text(strip=True)
                            min_clean = min_text.replace('.', '').replace(',', '.')
                            data['preco_min'] = float(min_clean)
                        except (ValueError, IndexError):
                            pass
                        
                        try:
                            # Extrai preço máximo
                            max_text = cells[4].get_text(strip=True)
                            max_clean = max_text.replace('.', '').replace(',', '.')
                            data['preco_max'] = float(max_clean)
                        except (ValueError, IndexError):
                            pass
            
            # Extrai informações do título (strike, vencimento)
            title = soup.find('h1')
            if title:
                title_text = title.get_text()
                # Exemplo: "PETRL311 - CALL de PETR4 - Strike R$ 30,50 - Vencimento 19/12/2025"
                
                # Extrai strike
                strike_match = re.search(r'Strike R\$\s*([\d,]+)', title_text)
                if strike_match:
                    strike_str = strike_match.group(1).replace(',', '.')
                    data['strike'] = float(strike_str)
                
                # Extrai vencimento
                venc_match = re.search(r'Vencimento\s*(\d{2}/\d{2}/\d{4})', title_text)
                if venc_match:
                    venc_str = venc_match.group(1)
                    data['vencimento'] = datetime.strptime(venc_str, '%d/%m/%Y')
                
                # Extrai tipo (CALL ou PUT)
                if 'CALL' in title_text.upper():
                    data['tipo'] = 'CALL'
                elif 'PUT' in title_text.upper():
                    data['tipo'] = 'PUT'
                
                # Extrai ação subjacente
                acao_match = re.search(r'(CALL|PUT)\s+de\s+([A-Z0-9]+)', title_text)
                if acao_match:
                    data['acao'] = acao_match.group(2)
            
            return data if 'preco_atual' in data else None
            
        except requests.RequestException as e:
            print(f"Erro ao consultar {url}: {e}")
            return None
        except Exception as e:
            print(f"Erro ao processar dados de {codigo_opcao}: {e}")
            return None
    
    def calcular_rendimento(
        self,
        preco_compra: float,
        preco_atual: float,
        quantidade: int = 1
    ) -> Dict:
        """
        Calcula rendimento de uma operação.
        
        Args:
            preco_compra: Preço de compra da opção
            preco_atual: Preço atual da opção
            quantidade: Quantidade de opções
        
        Returns:
            Dicionário com informações de rendimento
        """
        if preco_compra == 0:
            return {
                'erro': 'Preço de compra não pode ser zero'
            }
        
        variacao = preco_atual - preco_compra
        variacao_pct = (variacao / preco_compra) * 100
        valor_total = variacao * quantidade
        
        return {
            'preco_compra': preco_compra,
            'preco_atual': preco_atual,
            'variacao': variacao,
            'variacao_pct': variacao_pct,
            'quantidade': quantidade,
            'valor_total': valor_total,
            'lucro_prejuizo': valor_total  # Mesmo valor, mas nome mais claro
        }


def atualizar_preco_operacao(operation_id: str, codigo_opcao: str, preco_compra: float):
    """
    Atualiza o preço atual de uma operação consultando opcoes.net.br.
    
    Args:
        operation_id: ID da operação no banco
        codigo_opcao: Código da opção (ex: PETRL311)
        preco_compra: Preço de compra original
    """
    from ..storage import OperationDatabase
    
    collector = OpcoesNetCollector()
    db = OperationDatabase("mamhedge_operations.db")
    
    # Busca operação
    op = db.get_operation(operation_id)
    if not op:
        print(f"❌ Operação {operation_id} não encontrada.")
        return None
    
    # Consulta preço atual
    print(f"🔍 Consultando {codigo_opcao} em opcoes.net.br...")
    data = collector.get_option_data(codigo_opcao)
    
    if not data or 'preco_atual' not in data:
        print(f"❌ Não foi possível obter preço atual de {codigo_opcao}")
        return None
    
    preco_atual = data['preco_atual']
    
    # Calcula rendimento
    rendimento = collector.calcular_rendimento(preco_compra, preco_atual)
    
    # Atualiza operação
    op.preco_atual = preco_atual
    op.resultado_atual_pct = rendimento['variacao_pct']
    
    # Calcula distância do alvo (se houver)
    if op.alvo_saida:
        op.distancia_alvo = op.alvo_saida - preco_atual
    
    op.data_atualizacao = datetime.now()
    db.save_operation(op)
    
    print(f"✅ Preço atualizado!")
    print(f"   Preço Compra: R$ {preco_compra:.2f}")
    print(f"   Preço Atual: R$ {preco_atual:.2f}")
    print(f"   Variação: {rendimento['variacao_pct']:+.2f}%")
    print(f"   Valor: {rendimento['valor_total']:+.2f}")
    
    return rendimento


if __name__ == "__main__":
    # Teste
    collector = OpcoesNetCollector()
    
    # Testa com PETRL311
    print("Testando coleta de dados de PETRL311...")
    data = collector.get_option_data("PETRL311")
    
    if data:
        print("\n✅ Dados obtidos:")
        for key, value in data.items():
            print(f"   {key}: {value}")
    else:
        print("❌ Não foi possível obter dados.")

