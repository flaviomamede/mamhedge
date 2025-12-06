"""
Script para marcar todas as operações sugeridas como investidas em conta simulada
e consultar o opcoes.net.br para verificar o resultado após o fechamento do pregão.
"""

import sys
from pathlib import Path
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.data.storage import (
    OperationDatabase,
    OperationStatus,
    AccountType,
    ConsensoLevel,
    ConfiancaLevel
)
from src.data.collectors import OpcoesNetCollector


def marcar_todas_simulada_e_atualizar():
    """Marca todas as operações sugeridas como simulada e atualiza preços."""
    
    db = OperationDatabase("mamhedge_operations.db")
    collector = OpcoesNetCollector()
    
    # Busca operações sugeridas
    sugeridas = db.list_operations(status=OperationStatus.SUGERIDA)
    
    if not sugeridas:
        print("\n❌ Nenhuma operação sugerida encontrada.")
        return
    
    print("\n" + "=" * 80)
    print(f"ENCONTRADAS {len(sugeridas)} OPERAÇÕES SUGERIDAS")
    print("=" * 80)
    
    # Confirmação
    print("\n⚠️  ATENÇÃO: Todas as operações serão marcadas como investidas em CONTA SIMULADA")
    resposta = input("Deseja continuar? (s/N): ").strip().lower()
    
    if resposta != 's':
        print("Operação cancelada.")
        return
    
    resultados = []
    
    for i, op in enumerate(sugeridas, 1):
        terf = op.operacao_terf
        
        print(f"\n{'=' * 80}")
        print(f"OPERAÇÃO {i}/{len(sugeridas)}: {terf.acao}")
        print(f"{'=' * 80}")
        print(f"Call: {terf.codigo_call} (Strike R$ {terf.strike_call:.2f})")
        print(f"Put: {terf.codigo_put} (Strike R$ {terf.strike_put:.2f})")
        print(f"Rating: {terf.rating}")
        
        # Marca como investida em simulada
        op.consenso = ConsensoLevel.MEDIO  # Padrão para simulada
        op.confianca_ajustada = ConfiancaLevel.MEDIA
        op.marcar_investida(
            AccountType.SIMULADA,
            "Marcada automaticamente em conta simulada para teste"
        )
        
        # Consulta preços atuais
        print(f"\n🔍 Consultando preços atuais...")
        
        # Consulta Call
        print(f"   Consultando Call: {terf.codigo_call}...")
        call_data = collector.get_option_data(terf.codigo_call)
        
        # Consulta Put
        print(f"   Consultando Put: {terf.codigo_put}...")
        put_data = collector.get_option_data(terf.codigo_put)
        
        # Processa resultados
        resultado = {
            'operacao': op,
            'call_data': call_data,
            'put_data': put_data,
            'call_preco_compra': terf.valor_call,
            'put_preco_compra': terf.valor_put,
            'call_preco_atual': None,
            'put_preco_atual': None,
            'call_variacao_pct': None,
            'put_variacao_pct': None,
            'estrutura_resultado': None
        }
        
        if call_data and 'preco_atual' in call_data:
            call_preco_atual = call_data['preco_atual']
            resultado['call_preco_atual'] = call_preco_atual
            
            # Calcula variação da Call
            call_rend = collector.calcular_rendimento(terf.valor_call, call_preco_atual)
            resultado['call_variacao_pct'] = call_rend['variacao_pct']
            
            print(f"   ✅ Call: R$ {terf.valor_call:.2f} → R$ {call_preco_atual:.2f} ({call_rend['variacao_pct']:+.2f}%)")
        else:
            print(f"   ❌ Call: Não foi possível obter preço atual")
        
        if put_data and 'preco_atual' in put_data:
            put_preco_atual = put_data['preco_atual']
            resultado['put_preco_atual'] = put_preco_atual
            
            # Calcula variação da Put
            put_rend = collector.calcular_rendimento(terf.valor_put, put_preco_atual)
            resultado['put_variacao_pct'] = put_rend['variacao_pct']
            
            print(f"   ✅ Put: R$ {terf.valor_put:.2f} → R$ {put_preco_atual:.2f} ({put_rend['variacao_pct']:+.2f}%)")
        else:
            print(f"   ❌ Put: Não foi possível obter preço atual")
        
        # Calcula resultado da estrutura TERF
        # TERF: Compra Ação + Compra Put - Venda Call
        # Resultado = (Preço Ação Atual - Preço Ação Compra) + (Put Atual - Put Compra) - (Call Atual - Call Compra)
        # Simplificando: assumindo que a ação não mudou muito, focamos nas opções
        
        if resultado['call_preco_atual'] is not None and resultado['put_preco_atual'] is not None:
            # Custo inicial da estrutura (apenas opções)
            custo_inicial = terf.valor_put - terf.valor_call  # Put comprada, Call vendida
            
            # Valor atual da estrutura
            valor_atual = resultado['put_preco_atual'] - resultado['call_preco_atual']
            
            # Resultado da estrutura
            resultado_estrutura = valor_atual - custo_inicial
            resultado_pct = (resultado_estrutura / abs(custo_inicial)) * 100 if custo_inicial != 0 else 0
            
            resultado['estrutura_resultado'] = resultado_estrutura
            resultado['estrutura_resultado_pct'] = resultado_pct
            
            print(f"\n   📊 ESTRUTURA TERF:")
            print(f"      Custo Inicial: R$ {custo_inicial:.2f}")
            print(f"      Valor Atual: R$ {valor_atual:.2f}")
            print(f"      Resultado: R$ {resultado_estrutura:+.2f} ({resultado_pct:+.2f}%)")
        
        # Atualiza operação no banco
        if resultado['call_preco_atual'] is not None:
            op.preco_atual = resultado['call_preco_atual']  # Usa preço da Call como referência
            op.resultado_atual_pct = resultado['call_variacao_pct']
        
        op.data_atualizacao = datetime.now()
        db.save_operation(op)
        
        resultados.append(resultado)
        
        print(f"   💾 Operação salva no banco")
    
    # Relatório final
    print("\n" + "=" * 80)
    print("RELATÓRIO FINAL - RESULTADOS APÓS FECHAMENTO DO PREGÃO")
    print("=" * 80)
    
    for i, res in enumerate(resultados, 1):
        op = res['operacao']
        terf = op.operacao_terf
        
        print(f"\n{i}. {terf.acao} - Rating: {terf.rating}")
        print(f"   Call {terf.codigo_call}: ", end="")
        if res['call_variacao_pct'] is not None:
            sinal = "💰" if res['call_variacao_pct'] > 0 else "📉"
            print(f"{sinal} {res['call_variacao_pct']:+.2f}%")
        else:
            print("❌ Dados não disponíveis")
        
        print(f"   Put {terf.codigo_put}: ", end="")
        if res['put_variacao_pct'] is not None:
            sinal = "💰" if res['put_variacao_pct'] > 0 else "📉"
            print(f"{sinal} {res['put_variacao_pct']:+.2f}%")
        else:
            print("❌ Dados não disponíveis")
        
        if res['estrutura_resultado'] is not None:
            sinal = "💰" if res['estrutura_resultado'] > 0 else "📉"
            print(f"   Estrutura TERF: {sinal} R$ {res['estrutura_resultado']:+.2f} ({res['estrutura_resultado_pct']:+.2f}%)")
    
    # Estatísticas
    print("\n" + "=" * 80)
    print("ESTATÍSTICAS")
    print("=" * 80)
    
    call_sucesso = sum(1 for r in resultados if r['call_variacao_pct'] is not None and r['call_variacao_pct'] > 0)
    put_sucesso = sum(1 for r in resultados if r['put_variacao_pct'] is not None and r['put_variacao_pct'] > 0)
    estrutura_sucesso = sum(1 for r in resultados if r['estrutura_resultado'] is not None and r['estrutura_resultado'] > 0)
    
    print(f"\nCalls com lucro: {call_sucesso}/{len(resultados)}")
    print(f"Puts com lucro: {put_sucesso}/{len(resultados)}")
    print(f"Estruturas com lucro: {estrutura_sucesso}/{len(resultados)}")
    
    # Calcula lucro total e margem total
    estruturas_com_resultado = [r for r in resultados if r['estrutura_resultado'] is not None]
    
    if estruturas_com_resultado:
        lucro_total = sum(r['estrutura_resultado'] for r in estruturas_com_resultado)
        
        # Calcula custo total inicial das estruturas
        custo_total = 0
        for r in estruturas_com_resultado:
            op = r['operacao']
            terf = op.operacao_terf
            # Custo inicial = Put comprada - Call vendida
            custo_estrutura = terf.valor_put - terf.valor_call
            custo_total += abs(custo_estrutura)  # Usa valor absoluto para calcular margem
        
        # Calcula margem percentual total
        if custo_total > 0:
            margem_total_pct = (lucro_total / custo_total) * 100
        else:
            margem_total_pct = 0
        
        sinal = "💰" if lucro_total >= 0 else "📉"
        print(f"\n{sinal} Lucro total das estruturas: R$ {lucro_total:+.2f} ({margem_total_pct:+.2f}%)")


if __name__ == "__main__":
    print("=" * 80)
    print("MARCADOR AUTOMÁTICO - CONTA SIMULADA + ATUALIZAÇÃO DE PREÇOS")
    print("=" * 80)
    print("\nEste script irá:")
    print("1. Marcar todas as operações sugeridas como investidas em conta simulada")
    print("2. Consultar opcoes.net.br para obter preços atuais")
    print("3. Calcular resultado de cada estrutura TERF")
    print("4. Gerar relatório completo")
    
    marcar_todas_simulada_e_atualizar()

