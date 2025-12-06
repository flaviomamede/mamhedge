"""
Script para marcar travas com payoff > 1000% como investidas em conta simulada
e consultar o opcoes.net.br para verificar a margem após o fechamento do pregão.
"""

import sys
from pathlib import Path
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

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
from src.analysis import calcular_alocacao_travas


def marcar_travas_simulada_e_atualizar():
    """
    Marca travas como simulada baseado em ESPERANÇA ESTATÍSTICA (EV).
    
    Não filtra por payoff mínimo - considera TODAS as travas.
    Aloca capital proporcionalmente à esperança estatística.
    """
    
    # Parse travas do radar.md
    radar_path = Path(__file__).parent.parent.parent.parent / "radar.md"
    
    with open(radar_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    parser = TravaParser()
    travas = parser.parse_all_operations(text)
    
    if not travas:
        print("\n❌ Nenhuma trava encontrada no arquivo.")
        return
    
    print("\n" + "=" * 80)
    print(f"ENCONTRADAS {len(travas)} TRAVAS")
    print("=" * 80)
    
    # NÃO filtra por payoff - considera TODAS as travas
    # A alocação será baseada na esperança estatística (EV)
    travas_filtradas = travas
    
    if not travas_filtradas:
        print(f"\n❌ Nenhuma trava encontrada no arquivo.")
        return
    
    print(f"\n✅ {len(travas_filtradas)} travas encontradas")
    print(f"   Payoff mínimo: {min(t.payoff for t in travas):.2f}%")
    print(f"   Payoff máximo: {max(t.payoff for t in travas):.2f}%")
    print(f"\n💡 Alocação será baseada em ESPERANÇA ESTATÍSTICA (EV), não apenas em Payoff")
    print(f"   Travas com maior EV receberão mais capital, independente do Payoff")
    
    # Calcula alocações baseadas em esperança estatística
    print("\n" + "=" * 80)
    print("CALCULANDO ALOCAÇÕES BASEADAS EM ESPERANÇA ESTATÍSTICA")
    print("=" * 80)
    print("\n💡 Todas as travas serão avaliadas pela Esperança Estatística (EV)")
    print("   EV = (Probabilidade × Retorno_Positivo) + ((1-Prob) × Retorno_Negativo)")
    print("   Travas com EV positivo receberão alocação proporcional ao EV")
    
    # Pergunta capital disponível
    try:
        capital_input = input("\n💰 Capital total disponível para travas (R$): ").strip()
        capital_total = float(capital_input.replace('.', '').replace(',', '.'))
    except (ValueError, KeyboardInterrupt):
        print("Usando capital padrão de R$ 1.000,00")
        capital_total = 1000.0
    
    # Pergunta alpha heurística
    try:
        alpha_input = input("🎯 Alpha heurística (1.0 = mercado, 1.5 = robô melhora 50%, padrão 1.5): ").strip()
        alpha_heuristica = float(alpha_input) if alpha_input else 1.5
    except (ValueError, KeyboardInterrupt):
        alpha_heuristica = 1.5
    
    # Pergunta se quer filtrar apenas EV positivo
    try:
        filtrar_ev_input = input("🔍 Filtrar apenas travas com EV positivo? (S/n, padrão: S): ").strip().lower()
        filtrar_ev_positivo = filtrar_ev_input != 'n'
    except (ValueError, KeyboardInterrupt):
        filtrar_ev_positivo = True
    
    print(f"\nCalculando alocações...")
    alocacoes = calcular_alocacao_travas(
        travas_filtradas,
        capital_total,
        alpha_heuristica=alpha_heuristica,
        metodo="proporcional"
    )
    
    # Filtra travas com alocação > 0 (ou EV positivo se solicitado)
    if filtrar_ev_positivo:
        travas_com_alocacao = [aloc for aloc in alocacoes if aloc.alocacao_valor > 0]
    else:
        travas_com_alocacao = [aloc for aloc in alocacoes]
    
    if not travas_com_alocacao:
        print("\n❌ Nenhuma trava com alocação encontrada.")
        print("   Todas as travas têm EV negativo ou zero.")
        return
    
    # Mostra travas que serão marcadas com alocações
    print("\n" + "=" * 80)
    print(f"TRAVAS QUE SERÃO MARCADAS COMO SIMULADA ({len(travas_com_alocacao)} com alocação)")
    print("=" * 80)
    for i, aloc in enumerate(travas_com_alocacao, 1):
        if aloc.alocacao_valor > 0:
            trava = aloc.trava
            print(f"\n{i}. {trava.acao} - Payoff: {trava.payoff:.2f}% | Distância: {trava.distancia_ativo:.2f}%")
            print(f"   Comprada: {trava.codigo_comprada} (Strike R$ {trava.strike_comprada:.2f})")
            print(f"   Vendida: {trava.codigo_vendida} (Strike R$ {trava.strike_vendida:.2f})")
            print(f"   Probabilidade: {aloc.probabilidade_estimada:.2f}% | EV: {aloc.esperanca_estatistica:+.2f}%")
            print(f"   Alocação: {aloc.alocacao_pct:.2f}% = R$ {aloc.alocacao_valor:.2f}")
    
    # Filtra apenas travas com alocação > 0
    travas_filtradas = [aloc.trava for aloc in travas_com_alocacao if aloc.alocacao_valor > 0]
    alocacoes_dict = {aloc.trava: aloc for aloc in travas_com_alocacao if aloc.alocacao_valor > 0}
    
    # Confirmação
    print("\n⚠️  ATENÇÃO: Todas essas travas serão marcadas como investidas em CONTA SIMULADA")
    resposta = input("Deseja continuar? (s/N): ").strip().lower()
    
    if resposta != 's':
        print("Operação cancelada.")
        return
    
    db = OperationDatabase("mamhedge_operations.db")
    collector = OpcoesNetCollector()
    
    resultados = []
    
    for i, trava in enumerate(travas_filtradas, 1):
        aloc = alocacoes_dict.get(trava)
        
        print(f"\n{'=' * 80}")
        print(f"TRAVA {i}/{len(travas_filtradas)}: {trava.acao}")
        print(f"{'=' * 80}")
        print(f"Comprada: {trava.codigo_comprada} - Strike R$ {trava.strike_comprada:.2f}")
        print(f"Vendida: {trava.codigo_vendida} - Strike R$ {trava.strike_vendida:.2f}")
        print(f"Payoff: {trava.payoff:.2f}% | Distância: {trava.distancia_ativo:.2f}%")
        if aloc:
            print(f"Probabilidade: {aloc.probabilidade_estimada:.2f}% | EV: {aloc.esperanca_estatistica:+.2f}%")
            print(f"Alocação: {aloc.alocacao_pct:.2f}% = R$ {aloc.alocacao_valor:.2f}")
        
        # Busca alocação calculada
        aloc = alocacoes_dict.get(trava)
        
        # Cria RegisteredOperation a partir da TravaOperation
        # Como não temos TERFOperation, criamos uma estrutura similar
        notas = f"Trava: {trava.codigo_comprada}/{trava.codigo_vendida}, Payoff: {trava.payoff:.2f}%"
        if aloc:
            notas += f", Prob: {aloc.probabilidade_estimada:.2f}%, EV: {aloc.esperanca_estatistica:+.2f}%, Alocação: {aloc.alocacao_pct:.2f}%"
        
        reg_op = RegisteredOperation(
            id=None,  # Será gerado ao salvar
            operacao_terf=None,  # Travas não são TERFs
            estrategia=f"Trava {trava.tipo_trava}",
            probabilidade_app=aloc.probabilidade_estimada if aloc else None,
            consenso=ConsensoLevel.MEDIO,
            confianca_ajustada=ConfiancaLevel.MEDIA,
            status=OperationStatus.SUGERIDA,
            conta_tipo=None,
            data_decisao=None,
            motivo_decisao=None,
            custo_montagem=trava.custo_total,
            alvo_saida=None,
            preco_atual=None,
            resultado_atual_pct=None,
            distancia_alvo=None,
            decisao_hoje=None,
            data_saida=None,
            lucro_prejuizo_real=None,
            status_final=None,
            bayes_confirmou=None,
            notas=notas
        )
        
        # Gera ID único
        import uuid
        reg_op.id = str(uuid.uuid4())
        
        # Marca como investida em simulada
        reg_op.marcar_investida(
            AccountType.SIMULADA,
            f"Payoff {trava.payoff:.2f}% > 1000% - marcada automaticamente"
        )
        
        # Consulta preços atuais
        print(f"\n🔍 Consultando preços atuais...")
        
        # Consulta opção comprada
        print(f"   Consultando Comprada: {trava.codigo_comprada}...")
        comprada_data = collector.get_option_data(trava.codigo_comprada)
        
        # Consulta opção vendida
        print(f"   Consultando Vendida: {trava.codigo_vendida}...")
        vendida_data = collector.get_option_data(trava.codigo_vendida)
        
        # Processa resultados
        resultado = {
            'operacao': reg_op,
            'trava': trava,
            'comprada_data': comprada_data,
            'vendida_data': vendida_data,
            'comprada_preco_compra': trava.valor_comprada,
            'vendida_preco_compra': trava.valor_vendida,
            'comprada_preco_atual': None,
            'vendida_preco_atual': None,
            'comprada_variacao_pct': None,
            'vendida_variacao_pct': None,
            'trava_resultado': None,
            'trava_resultado_pct': None
        }
        
        if comprada_data and 'preco_atual' in comprada_data:
            comprada_preco_atual = comprada_data['preco_atual']
            resultado['comprada_preco_atual'] = comprada_preco_atual
            
            # Calcula variação da opção comprada
            comprada_rend = collector.calcular_rendimento(trava.valor_comprada, comprada_preco_atual)
            resultado['comprada_variacao_pct'] = comprada_rend['variacao_pct']
            
            print(f"   ✅ Comprada: R$ {trava.valor_comprada:.2f} → R$ {comprada_preco_atual:.2f} ({comprada_rend['variacao_pct']:+.2f}%)")
        else:
            print(f"   ❌ Comprada: Não foi possível obter preço atual")
        
        if vendida_data and 'preco_atual' in vendida_data:
            vendida_preco_atual = vendida_data['preco_atual']
            resultado['vendida_preco_atual'] = vendida_preco_atual
            
            # Calcula variação da opção vendida
            # Quando vendemos, ganhamos quando o preço cai
            # Variação = (Preço Venda - Preço Atual) / Preço Venda
            variacao_vendida = ((trava.valor_vendida - vendida_preco_atual) / trava.valor_vendida) * 100 if trava.valor_vendida > 0 else 0
            resultado['vendida_variacao_pct'] = variacao_vendida
            
            print(f"   ✅ Vendida: R$ {trava.valor_vendida:.2f} → R$ {vendida_preco_atual:.2f} ({variacao_vendida:+.2f}%)")
        else:
            print(f"   ❌ Vendida: Não foi possível obter preço atual")
        
        # Calcula resultado da trava
        # Trava: Compra opção A (comprada), Vende opção B (vendida)
        # Para opção comprada: lucro quando valor sobe
        # Para opção vendida: lucro quando valor desce (invertido)
        # Resultado = (Valor Atual A - Valor Compra A) + (Valor Compra B - Valor Atual B)
        # Simplificando: (Atual A - Atual B) - (Compra A - Compra B)
        
        if resultado['comprada_preco_atual'] is not None and resultado['vendida_preco_atual'] is not None:
            # Custo inicial da trava (o que pagamos para montar)
            custo_inicial = trava.valor_comprada - trava.valor_vendida
            
            # Valor atual da trava (spread atual)
            valor_atual = resultado['comprada_preco_atual'] - resultado['vendida_preco_atual']
            
            # Resultado da trava = valor atual - custo inicial
            resultado_trava = valor_atual - custo_inicial
            resultado_pct = (resultado_trava / abs(custo_inicial)) * 100 if custo_inicial != 0 else 0
            
            resultado['trava_resultado'] = resultado_trava
            resultado['trava_resultado_pct'] = resultado_pct
            
            print(f"\n   📊 TRAVA:")
            print(f"      Custo Inicial: R$ {custo_inicial:.2f}")
            print(f"      Valor Atual: R$ {valor_atual:.2f}")
            print(f"      Resultado: R$ {resultado_trava:+.2f} ({resultado_pct:+.2f}%)")
            
            # Atualiza operação
            reg_op.preco_atual = valor_atual
            reg_op.resultado_atual_pct = resultado_pct
        
        reg_op.data_atualizacao = datetime.now()
        db.save_operation(reg_op)
        
        resultados.append(resultado)
        
        print(f"   💾 Operação salva no banco")
    
    # Relatório final
    print("\n" + "=" * 80)
    print("RELATÓRIO FINAL - MARGEM APÓS FECHAMENTO DO PREGÃO")
    print("=" * 80)
    
    for i, res in enumerate(resultados, 1):
        trava = res['trava']
        aloc = alocacoes_dict.get(trava)
        
        print(f"\n{i}. {trava.acao} - Payoff: {trava.payoff:.2f}% | Distância: {trava.distancia_ativo:.2f}%")
        if aloc:
            print(f"   Probabilidade: {aloc.probabilidade_estimada:.2f}% | EV: {aloc.esperanca_estatistica:+.2f}% | Alocação: {aloc.alocacao_pct:.2f}%")
        print(f"   Comprada {trava.codigo_comprada}: ", end="")
        if res['comprada_variacao_pct'] is not None:
            sinal = "💰" if res['comprada_variacao_pct'] > 0 else "📉"
            print(f"{sinal} {res['comprada_variacao_pct']:+.2f}%")
        else:
            print("❌ Dados não disponíveis")
        
        print(f"   Vendida {trava.codigo_vendida}: ", end="")
        if res['vendida_variacao_pct'] is not None:
            sinal = "💰" if res['vendida_variacao_pct'] > 0 else "📉"
            print(f"{sinal} {res['vendida_variacao_pct']:+.2f}%")
        else:
            print("❌ Dados não disponíveis")
        
        if res['trava_resultado'] is not None:
            sinal = "💰" if res['trava_resultado'] > 0 else "📉"
            # Calcula resultado considerando a alocação
            if aloc and aloc.alocacao_valor > 0:
                resultado_alocado = res['trava_resultado'] * (aloc.alocacao_valor / trava.custo_total) if trava.custo_total > 0 else 0
                print(f"   Trava: {sinal} R$ {res['trava_resultado']:+.2f} ({res['trava_resultado_pct']:+.2f}%)")
                print(f"   Resultado na Alocação: {sinal} R$ {resultado_alocado:+.2f}")
            else:
                print(f"   Trava: {sinal} R$ {res['trava_resultado']:+.2f} ({res['trava_resultado_pct']:+.2f}%)")
    
    # Estatísticas
    print("\n" + "=" * 80)
    print("ESTATÍSTICAS")
    print("=" * 80)
    
    comprada_sucesso = sum(1 for r in resultados if r['comprada_variacao_pct'] is not None and r['comprada_variacao_pct'] > 0)
    vendida_sucesso = sum(1 for r in resultados if r['vendida_variacao_pct'] is not None and r['vendida_variacao_pct'] > 0)
    trava_sucesso = sum(1 for r in resultados if r['trava_resultado'] is not None and r['trava_resultado'] > 0)
    
    print(f"\nOpções Compradas com lucro: {comprada_sucesso}/{len(resultados)}")
    print(f"Opções Vendidas com lucro: {vendida_sucesso}/{len(resultados)}")
    print(f"Travas com lucro: {trava_sucesso}/{len(resultados)}")
    
    # Calcula lucro total e margem total (considerando alocações)
    travas_com_resultado = [r for r in resultados if r['trava_resultado'] is not None]
    
    if travas_com_resultado:
        # Lucro total unitário (por trava)
        lucro_total_unitario = sum(r['trava_resultado'] for r in travas_com_resultado)
        
        # Lucro total considerando alocações
        lucro_total_alocado = 0.0
        custo_total_alocado = 0.0
        
        for r in travas_com_resultado:
            trava = r['trava']
            aloc = alocacoes_dict.get(trava)
            
            if aloc and aloc.alocacao_valor > 0:
                # Quantidade de travas compradas com a alocação
                quantidade = int(aloc.alocacao_valor / trava.custo_total) if trava.custo_total > 0 else 0
                # Resultado total para essa alocação
                resultado_alocado = r['trava_resultado'] * quantidade
                lucro_total_alocado += resultado_alocado
                custo_total_alocado += aloc.alocacao_valor
        
        # Calcula margem percentual total
        if custo_total_alocado > 0:
            margem_total_pct = (lucro_total_alocado / custo_total_alocado) * 100
        else:
            margem_total_pct = 0
        
        sinal = "💰" if lucro_total_alocado >= 0 else "📉"
        print(f"\n{sinal} Lucro total das travas (unitário): R$ {lucro_total_unitario:+.2f}")
        print(f"{sinal} Lucro total das travas (com alocações): R$ {lucro_total_alocado:+.2f} ({margem_total_pct:+.2f}%)")
        print(f"   Capital alocado: R$ {custo_total_alocado:.2f}")


if __name__ == "__main__":
    print("=" * 80)
    print("MARCADOR DE TRAVAS - CONTA SIMULADA + ATUALIZAÇÃO DE PREÇOS")
    print("=" * 80)
    print("\nEste script irá:")
    print("1. Parsear TODAS as travas do radar.md")
    print("2. Calcular Esperança Estatística (EV) para cada trava")
    print("3. Alocar capital proporcionalmente ao EV (não apenas ao Payoff)")
    print("4. Marcar travas com EV positivo como investidas em conta simulada")
    print("5. Consultar opcoes.net.br para obter preços atuais")
    print("6. Calcular margem após fechamento do pregão")
    print("7. Gerar relatório completo")
    print("\n💡 IMPORTANTE: Travas com Payoff menor podem ter maior EV")
    print("   se tiverem maior probabilidade (menor distância do ativo)")
    
    marcar_travas_simulada_e_atualizar()

