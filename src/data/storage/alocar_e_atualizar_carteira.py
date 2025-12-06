"""
Script integrado para alocar capital entre TERFs e Travas e atualizar preços.

Distribuição padrão:
- 95% em TERFs
- 5% em Travas

Aloca baseado em esperança estatística para ambos.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.data.parsers.everhedge_parser import EverHedgeParser, TERFOperation
from src.data.parsers.trava_parser import TravaParser
from src.data.storage import (
    OperationDatabase,
    OperationStatus,
    AccountType,
    ConsensoLevel,
    ConfiancaLevel,
    RegisteredOperation
)
from src.data.collectors import OpcoesNetCollector
from src.analysis import calcular_alocacao_terfs, calcular_alocacao_travas


def formatar_moeda(valor: float) -> str:
    """Formata valor como moeda brasileira."""
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def alocar_e_atualizar_carteira(
    capital_total: float,
    pct_terfs: float = 95.0,
    pct_travas: float = 5.0,
    alpha_heuristica_terf: float = 1.0,
    alpha_heuristica_trava: float = 1.5
):
    """
    Aloca capital entre TERFs e Travas e atualiza preços.
    
    Args:
        capital_total: Capital total disponível
        pct_terfs: Porcentagem para TERFs (padrão: 95%)
        pct_travas: Porcentagem para Travas (padrão: 5%)
        alpha_heuristica_terf: Alpha para TERFs (padrão: 1.0)
        alpha_heuristica_trava: Alpha para Travas (padrão: 1.5)
    """
    print("=" * 100)
    print("ALOCAÇÃO E ATUALIZAÇÃO DE CARTEIRA - TERFs E TRAVAS")
    print("=" * 100)
    
    # Calcula capital por tipo
    capital_terfs = capital_total * (pct_terfs / 100.0)
    capital_travas = capital_total * (pct_travas / 100.0)
    
    print(f"\n💰 Capital Total: {formatar_moeda(capital_total)}")
    print(f"   TERFs ({pct_terfs}%): {formatar_moeda(capital_terfs)}")
    print(f"   Travas ({pct_travas}%): {formatar_moeda(capital_travas)}")
    
    # Parse operações
    radar_path = Path(__file__).parent.parent.parent.parent / "radar.md"
    
    with open(radar_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Parse TERFs
    print("\n" + "=" * 100)
    print("PARSEANDO TERFs")
    print("=" * 100)
    parser_terf = EverHedgeParser()
    terfs = parser_terf.parse_all_operations(text)
    print(f"✅ {len(terfs)} TERFs encontradas")
    
    # Parse Travas
    print("\n" + "=" * 100)
    print("PARSEANDO TRAVAS")
    print("=" * 100)
    parser_trava = TravaParser()
    travas = parser_trava.parse_all_operations(text)
    print(f"✅ {len(travas)} Travas encontradas")
    
    # Calcula alocações
    print("\n" + "=" * 100)
    print("CALCULANDO ALOCAÇÕES BASEADAS EM ESPERANÇA ESTATÍSTICA")
    print("=" * 100)
    
    print(f"\n📊 TERFs (Alpha: {alpha_heuristica_terf})...")
    alocacoes_terf = calcular_alocacao_terfs(
        terfs,
        capital_terfs,
        alpha_heuristica=alpha_heuristica_terf,
        metodo="proporcional"
    )
    terfs_com_alocacao = [a for a in alocacoes_terf if a.alocacao_valor > 0]
    print(f"   {len(terfs_com_alocacao)} TERFs com alocação")
    
    print(f"\n📊 Travas (Alpha: {alpha_heuristica_trava})...")
    alocacoes_trava = calcular_alocacao_travas(
        travas,
        capital_travas,
        alpha_heuristica=alpha_heuristica_trava,
        metodo="proporcional"
    )
    travas_com_alocacao = [a for a in alocacoes_trava if a.alocacao_valor > 0]
    print(f"   {len(travas_com_alocacao)} Travas com alocação")
    
    # Mostra alocações
    print("\n" + "=" * 100)
    print("ALOCAÇÕES CALCULADAS")
    print("=" * 100)
    
    print(f"\n📈 TERFs ({len(terfs_com_alocacao)} com alocação):")
    for i, aloc in enumerate(terfs_com_alocacao[:5], 1):  # Mostra top 5
        terf = aloc.terf
        print(f"   {i}. {terf.acao} - Rating: {terf.rating} | Prob: {aloc.probabilidade_estimada:.2f}% | EV: {aloc.esperanca_estatistica:+.2f}%")
        print(f"      Alocação: {aloc.alocacao_pct:.2f}% = {formatar_moeda(aloc.alocacao_valor)}")
    
    print(f"\n📉 Travas ({len(travas_com_alocacao)} com alocação):")
    for i, aloc in enumerate(travas_com_alocacao[:5], 1):  # Mostra top 5
        trava = aloc.trava
        print(f"   {i}. {trava.acao} - Payoff: {trava.payoff:.2f}% | Prob: {aloc.probabilidade_estimada:.2f}% | EV: {aloc.esperanca_estatistica:+.2f}%")
        print(f"      Alocação: {aloc.alocacao_pct:.2f}% = {formatar_moeda(aloc.alocacao_valor)}")
    
    # Confirmação
    print("\n⚠️  ATENÇÃO: Todas essas operações serão marcadas como investidas em CONTA SIMULADA")
    resposta = input("Deseja continuar e consultar preços? (s/N): ").strip().lower()
    
    if resposta != 's':
        print("Operação cancelada.")
        return
    
    # Consulta preços e atualiza
    db = OperationDatabase("mamhedge_operations.db")
    collector = OpcoesNetCollector()
    
    resultados_terf = []
    resultados_trava = []
    
    # Processa TERFs
    print("\n" + "=" * 100)
    print("CONSULTANDO PREÇOS - TERFs")
    print("=" * 100)
    
    for i, aloc in enumerate(terfs_com_alocacao, 1):
        terf = aloc.terf
        print(f"\n{i}/{len(terfs_com_alocacao)}. {terf.acao} - {terf.codigo_call}/{terf.codigo_put}")
        
        # Consulta preços
        print(f"   Consultando Call {terf.codigo_call}...")
        call_data = collector.get_option_data(terf.codigo_call)
        
        print(f"   Consultando Put {terf.codigo_put}...")
        put_data = collector.get_option_data(terf.codigo_put)
        
        # Calcula resultado da TERF
        # TERF: Compra Ação + Compra Put - Venda Call
        # Resultado = (Put Atual - Put Compra) - (Call Atual - Call Compra)
        # Simplificando: (Put Atual - Call Atual) - (Put Compra - Call Compra)
        
        resultado = {
            'terf': terf,
            'alocacao': aloc,
            'call_data': call_data,
            'put_data': put_data,
            'call_preco_atual': None,
            'put_preco_atual': None,
            'estrutura_resultado': None,
            'estrutura_resultado_pct': None,
            'resultado_alocado': None
        }
        
        if call_data and 'preco_atual' in call_data:
            resultado['call_preco_atual'] = call_data['preco_atual']
        
        if put_data and 'preco_atual' in put_data:
            resultado['put_preco_atual'] = put_data['preco_atual']
        
        # Calcula resultado da estrutura TERF
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
            
            # Resultado considerando alocação
            # Quantidade de estruturas que pode comprar com a alocação
            quantidade = int(aloc.alocacao_valor / terf.coeficiente) if terf.coeficiente > 0 else 0
            resultado['resultado_alocado'] = resultado_estrutura * quantidade
            
            print(f"   📊 ESTRUTURA TERF:")
            print(f"      Custo Inicial: R$ {custo_inicial:.2f}")
            print(f"      Valor Atual: R$ {valor_atual:.2f}")
            print(f"      Resultado Unitário: R$ {resultado_estrutura:+.2f} ({resultado_pct:+.2f}%)")
            if quantidade > 0:
                print(f"      Quantidade: {quantidade} estruturas")
                print(f"      Resultado Total: R$ {resultado['resultado_alocado']:+.2f}")
        
        resultados_terf.append(resultado)
        
        # Salva no banco
        reg_op = RegisteredOperation(
            id=None,
            operacao_terf=terf,
            estrategia="TERF",
            probabilidade_app=aloc.probabilidade_estimada,
            consenso=ConsensoLevel.MEDIO,
            confianca_ajustada=ConfiancaLevel.MEDIA,
            status=OperationStatus.SUGERIDA,
            conta_tipo=None,
            data_decisao=None,
            motivo_decisao=None,
            custo_montagem=terf.coeficiente,
            alvo_saida=None,
            preco_atual=resultado.get('estrutura_resultado'),
            resultado_atual_pct=resultado.get('estrutura_resultado_pct'),
            distancia_alvo=None,
            decisao_hoje=None,
            data_saida=None,
            lucro_prejuizo_real=None,
            status_final=None,
            bayes_confirmou=None,
            notas=f"TERF: Prob {aloc.probabilidade_estimada:.2f}%, EV {aloc.esperanca_estatistica:+.2f}%, Alocação {aloc.alocacao_pct:.2f}%"
        )
        
        import uuid
        reg_op.id = str(uuid.uuid4())
        reg_op.marcar_investida(
            AccountType.SIMULADA,
            f"Alocação automática baseada em EV {aloc.esperanca_estatistica:+.2f}%"
        )
        reg_op.data_atualizacao = datetime.now()
        db.save_operation(reg_op)
    
    # Processa Travas
    print("\n" + "=" * 100)
    print("CONSULTANDO PREÇOS - TRAVAS")
    print("=" * 100)
    
    for i, aloc in enumerate(travas_com_alocacao, 1):
        trava = aloc.trava
        print(f"\n{i}/{len(travas_com_alocacao)}. {trava.acao} - {trava.codigo_comprada}/{trava.codigo_vendida}")
        
        # Consulta preços
        print(f"   Consultando Comprada {trava.codigo_comprada}...")
        comprada_data = collector.get_option_data(trava.codigo_comprada)
        
        print(f"   Consultando Vendida {trava.codigo_vendida}...")
        vendida_data = collector.get_option_data(trava.codigo_vendida)
        
        # Calcula resultado da trava
        resultado = {
            'trava': trava,
            'alocacao': aloc,
            'comprada_data': comprada_data,
            'vendida_data': vendida_data,
            'comprada_preco_atual': None,
            'vendida_preco_atual': None,
            'trava_resultado': None,
            'trava_resultado_pct': None,
            'resultado_alocado': None
        }
        
        if comprada_data and 'preco_atual' in comprada_data:
            resultado['comprada_preco_atual'] = comprada_data['preco_atual']
        
        if vendida_data and 'preco_atual' in vendida_data:
            resultado['vendida_preco_atual'] = vendida_data['preco_atual']
        
        # Calcula resultado da trava
        if resultado['comprada_preco_atual'] is not None and resultado['vendida_preco_atual'] is not None:
            custo_inicial = trava.valor_comprada - trava.valor_vendida
            valor_atual = resultado['comprada_preco_atual'] - resultado['vendida_preco_atual']
            resultado_trava = valor_atual - custo_inicial
            resultado_pct = (resultado_trava / abs(custo_inicial)) * 100 if custo_inicial != 0 else 0
            
            resultado['trava_resultado'] = resultado_trava
            resultado['trava_resultado_pct'] = resultado_pct
            
            # Resultado considerando alocação
            quantidade = int(aloc.alocacao_valor / trava.custo_total) if trava.custo_total > 0 else 0
            resultado['resultado_alocado'] = resultado_trava * quantidade
        
        resultados_trava.append(resultado)
        
        # Salva no banco
        reg_op = RegisteredOperation(
            id=None,
            operacao_terf=None,
            estrategia=f"Trava {trava.tipo_trava}",
            probabilidade_app=aloc.probabilidade_estimada,
            consenso=ConsensoLevel.MEDIO,
            confianca_ajustada=ConfiancaLevel.MEDIA,
            status=OperationStatus.SUGERIDA,
            conta_tipo=None,
            data_decisao=None,
            motivo_decisao=None,
            custo_montagem=trava.custo_total,
            alvo_saida=None,
            preco_atual=resultado.get('trava_resultado'),
            resultado_atual_pct=resultado.get('trava_resultado_pct'),
            distancia_alvo=None,
            decisao_hoje=None,
            data_saida=None,
            lucro_prejuizo_real=None,
            status_final=None,
            bayes_confirmou=None,
            notas=f"Trava: Prob {aloc.probabilidade_estimada:.2f}%, EV {aloc.esperanca_estatistica:+.2f}%, Alocação {aloc.alocacao_pct:.2f}%"
        )
        
        import uuid
        reg_op.id = str(uuid.uuid4())
        reg_op.marcar_investida(
            AccountType.SIMULADA,
            f"Alocação automática baseada em EV {aloc.esperanca_estatistica:+.2f}%"
        )
        reg_op.data_atualizacao = datetime.now()
        db.save_operation(reg_op)
    
    # Resumo final agrupado
    print("\n" + "=" * 100)
    print("RESUMO FINAL - MARGEM APÓS FECHAMENTO DO PREGÃO")
    print("=" * 100)
    
    # Resumo TERFs
    print(f"\n📈 TERFs ({len(resultados_terf)} operações):")
    capital_terf_alocado = sum(a.alocacao_valor for a in terfs_com_alocacao)
    lucro_total_terfs = sum(r.get('resultado_alocado', 0) for r in resultados_terf if r.get('resultado_alocado') is not None)
    
    print(f"   Capital Alocado: {formatar_moeda(capital_terf_alocado)}")
    if capital_terf_alocado > 0:
        margem_terfs_pct = (lucro_total_terfs / capital_terf_alocado) * 100
        sinal = "💰" if lucro_total_terfs >= 0 else "📉"
        print(f"   {sinal} Lucro Total: {formatar_moeda(lucro_total_terfs)} ({margem_terfs_pct:+.2f}%)")
    
    # Resumo Travas
    print(f"\n📉 Travas ({len(resultados_trava)} operações):")
    capital_trava_alocado = sum(a.alocacao_valor for a in travas_com_alocacao)
    lucro_total_travas = sum(r.get('resultado_alocado', 0) for r in resultados_trava if r.get('resultado_alocado') is not None)
    
    print(f"   Capital Alocado: {formatar_moeda(capital_trava_alocado)}")
    if capital_trava_alocado > 0:
        margem_travas_pct = (lucro_total_travas / capital_trava_alocado) * 100
        sinal = "💰" if lucro_total_travas >= 0 else "📉"
        print(f"   {sinal} Lucro Total: {formatar_moeda(lucro_total_travas)} ({margem_travas_pct:+.2f}%)")
    
    # Resumo Geral
    print(f"\n💰 RESUMO GERAL DA CARTEIRA:")
    capital_total_alocado = capital_terf_alocado + capital_trava_alocado
    lucro_total_geral = lucro_total_terfs + lucro_total_travas
    
    print(f"   Capital Total Alocado: {formatar_moeda(capital_total_alocado)}")
    if capital_total_alocado > 0:
        print(f"      TERFs: {formatar_moeda(capital_terf_alocado)} ({capital_terf_alocado/capital_total_alocado*100:.1f}%)")
        print(f"      Travas: {formatar_moeda(capital_trava_alocado)} ({capital_trava_alocado/capital_total_alocado*100:.1f}%)")
    
    sinal_geral = "💰" if lucro_total_geral >= 0 else "📉"
    print(f"\n   {sinal_geral} Lucro Total: {formatar_moeda(lucro_total_geral)}")
    print(f"      TERFs: {formatar_moeda(lucro_total_terfs)}")
    print(f"      Travas: {formatar_moeda(lucro_total_travas)}")
    
    if capital_total_alocado > 0:
        margem_geral_pct = (lucro_total_geral / capital_total_alocado) * 100
        print(f"   {sinal_geral} Margem Total: {margem_geral_pct:+.2f}%")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Alocar capital entre TERFs e Travas')
    parser.add_argument('--capital', type=float, default=100000.0, help='Capital total (padrão: R$ 100.000)')
    parser.add_argument('--pct-terfs', type=float, default=95.0, help='% para TERFs (padrão: 95%)')
    parser.add_argument('--pct-travas', type=float, default=5.0, help='% para Travas (padrão: 5%)')
    parser.add_argument('--alpha-terf', type=float, default=1.0, help='Alpha heurística TERFs (padrão: 1.0)')
    parser.add_argument('--alpha-trava', type=float, default=1.5, help='Alpha heurística Travas (padrão: 1.5)')
    
    args = parser.parse_args()
    
    alocar_e_atualizar_carteira(
        capital_total=args.capital,
        pct_terfs=args.pct_terfs,
        pct_travas=args.pct_travas,
        alpha_heuristica_terf=args.alpha_terf,
        alpha_heuristica_trava=args.alpha_trava
    )

