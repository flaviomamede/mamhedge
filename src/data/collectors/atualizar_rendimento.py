"""
Script para atualizar rendimento de operações consultando opcoes.net.br.

Uso:
    python atualizar_rendimento.py [operation_id] [codigo_opcao]
    
Exemplo:
    python atualizar_rendimento.py abc123 PETRL311
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.data.storage import OperationDatabase, OperationStatus
from src.data.collectors import OpcoesNetCollector


def atualizar_operacao_interativa():
    """Interface interativa para atualizar rendimento."""
    from datetime import datetime
    
    db = OperationDatabase("mamhedge_operations.db")
    collector = OpcoesNetCollector()
    
    # Lista operações investidas
    reais = db.list_operations(status=OperationStatus.INVESTIDA_REAL)
    simuladas = db.list_operations(status=OperationStatus.INVESTIDA_SIMULADA)
    
    todas_investidas = reais + simuladas
    
    if not todas_investidas:
        print("\n❌ Nenhuma operação investida encontrada.")
        return
    
    print("\n" + "=" * 80)
    print("OPERAÇÕES INVESTIDAS")
    print("=" * 80)
    
    for i, op in enumerate(todas_investidas, 1):
        terf = op.operacao_terf
        conta = "REAL" if op.conta_tipo.value == "real" else "SIMULADA"
        print(f"\n{i}. ID: {op.id[:8]}... | Conta: {conta}")
        print(f"   Ação: {terf.acao}")
        print(f"   Call: {terf.codigo_call}")
        print(f"   Put: {terf.codigo_put}")
        if op.preco_atual:
            print(f"   Preço Atual: R$ {op.preco_atual:.2f} | Resultado: {op.resultado_atual_pct:+.2f}%")
    
    # Seleciona operação
    try:
        escolha = int(input("\nEscolha o número da operação (ou 0 para cancelar): "))
        if escolha == 0 or escolha > len(todas_investidas):
            print("Operação cancelada.")
            return
        
        op = todas_investidas[escolha - 1]
        terf = op.operacao_terf
        
        # Pergunta qual opção atualizar
        print(f"\nQual opção você quer atualizar?")
        print(f"1. Call: {terf.codigo_call}")
        print(f"2. Put: {terf.codigo_put}")
        
        opcao_escolha = input("Escolha (1 ou 2): ").strip()
        
        if opcao_escolha == '1':
            codigo = terf.codigo_call
            preco_compra = terf.valor_call
        elif opcao_escolha == '2':
            codigo = terf.codigo_put
            preco_compra = terf.valor_put
        else:
            print("Opção inválida.")
            return
        
        # Consulta preço
        print(f"\n🔍 Consultando {codigo} em opcoes.net.br...")
        data = collector.get_option_data(codigo)
        
        if not data or 'preco_atual' not in data:
            print(f"❌ Não foi possível obter preço atual de {codigo}")
            print("   Verifique se o código está correto e tente novamente.")
            return
        
        preco_atual = data['preco_atual']
        
        # Calcula rendimento
        rendimento = collector.calcular_rendimento(preco_compra, preco_atual)
        
        # Atualiza operação
        op.preco_atual = preco_atual
        op.resultado_atual_pct = rendimento['variacao_pct']
        op.data_atualizacao = datetime.now()
        db.save_operation(op)
        
        # Mostra resultado
        print("\n" + "=" * 80)
        print("✅ PREÇO ATUALIZADO")
        print("=" * 80)
        print(f"Opção: {codigo}")
        print(f"Preço Compra: R$ {preco_compra:.2f}")
        print(f"Preço Atual: R$ {preco_atual:.2f}")
        print(f"Variação: {rendimento['variacao_pct']:+.2f}%")
        print(f"Valor: R$ {rendimento['variacao']:+.2f}")
        
        if rendimento['variacao_pct'] > 0:
            print(f"\n💰 LUCRO de {rendimento['variacao_pct']:.2f}%")
        else:
            print(f"\n📉 PREJUÍZO de {abs(rendimento['variacao_pct']):.2f}%")
        
    except (ValueError, KeyboardInterrupt):
        print("\nOperação cancelada.")
    except Exception as e:
        print(f"\n❌ Erro: {e}")


if __name__ == "__main__":
    from datetime import datetime
    
    print("=" * 80)
    print("ATUALIZADOR DE RENDIMENTO - MamHedge")
    print("=" * 80)
    atualizar_operacao_interativa()

