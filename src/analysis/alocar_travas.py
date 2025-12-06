"""
Script para calcular alocação de capital entre travas baseado em esperança estatística.

Uso:
    python alocar_travas.py [--capital CAPITAL] [--alpha ALPHA] [--metodo METODO]
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List

# Adiciona o diretório raiz ao path
root_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_path))

# Imports relativos
from src.data.parsers.trava_parser import TravaParser
try:
    from src.analysis import calcular_alocacao_travas, AlocacaoTrava
except ImportError:
    # Se não conseguir importar, importa diretamente
    from esperanca_estatistica import calcular_alocacao_travas, AlocacaoTrava


def formatar_moeda(valor: float) -> str:
    """Formata valor como moeda brasileira."""
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def mostrar_alocacoes(alocacoes: List[AlocacaoTrava], capital_total: float):
    """Mostra relatório de alocações."""
    
    # Filtra apenas travas com alocação
    alocacoes_ativas = [a for a in alocacoes if a.alocacao_valor > 0]
    
    if not alocacoes_ativas:
        print("\n❌ Nenhuma trava com esperança estatística positiva encontrada.")
        print("   Todas as travas têm EV negativo ou zero.")
        return
    
    print("\n" + "=" * 100)
    print("ALOCAÇÃO DE CAPITAL BASEADA EM ESPERANÇA ESTATÍSTICA")
    print("=" * 100)
    
    print(f"\nCapital Total Disponível: {formatar_moeda(capital_total)}")
    print(f"Travas com Alocação: {len(alocacoes_ativas)}")
    
    capital_alocado = sum(a.alocacao_valor for a in alocacoes_ativas)
    print(f"Capital Alocado: {formatar_moeda(capital_alocado)} ({capital_alocado/capital_total*100:.2f}%)")
    print(f"Capital Não Alocado: {formatar_moeda(capital_total - capital_alocado)}")
    
    print("\n" + "=" * 100)
    print("DETALHAMENTO POR TRAVA")
    print("=" * 100)
    
    for i, aloc in enumerate(alocacoes_ativas, 1):
        trava = aloc.trava
        
        print(f"\n{i}. {trava.acao} - {trava.codigo_comprada}/{trava.codigo_vendida}")
        print(f"   Payoff: {trava.payoff:.2f}% | Distância: {trava.distancia_ativo:.2f}% | Custo: {formatar_moeda(trava.custo_total)}")
        print(f"   Probabilidade Estimada: {aloc.probabilidade_estimada:.2f}%")
        print(f"   Esperança Estatística (EV): {aloc.esperanca_estatistica:+.2f}%")
        print(f"   Alocação: {aloc.alocacao_pct:.2f}% = {formatar_moeda(aloc.alocacao_valor)}")
        print(f"   Retorno Esperado: {formatar_moeda(aloc.retorno_esperado)}")
        
        # Quantidade de travas que pode comprar
        quantidade = int(aloc.alocacao_valor / trava.custo_total) if trava.custo_total > 0 else 0
        print(f"   Quantidade: {quantidade} travas (custo unitário: {formatar_moeda(trava.custo_total)})")
    
    # Estatísticas
    print("\n" + "=" * 100)
    print("ESTATÍSTICAS")
    print("=" * 100)
    
    ev_medio = sum(a.esperanca_estatistica for a in alocacoes_ativas) / len(alocacoes_ativas)
    prob_media = sum(a.probabilidade_estimada for a in alocacoes_ativas) / len(alocacoes_ativas)
    retorno_esperado_total = sum(a.retorno_esperado for a in alocacoes_ativas)
    
    print(f"\nEsperança Estatística Média: {ev_medio:+.2f}%")
    print(f"Probabilidade Média: {prob_media:.2f}%")
    print(f"Retorno Esperado Total: {formatar_moeda(retorno_esperado_total)}")
    print(f"Retorno Esperado %: {(retorno_esperado_total / capital_total) * 100:+.2f}%")
    
    # Mostra travas não alocadas (EV negativo)
    travas_nao_alocadas = [a for a in alocacoes if a.alocacao_valor == 0 and a.esperanca_estatistica <= 0]
    if travas_nao_alocadas:
        print(f"\n⚠️  {len(travas_nao_alocadas)} travas NÃO alocadas (EV negativo ou zero):")
        for aloc in travas_nao_alocadas[:5]:  # Mostra até 5
            trava = aloc.trava
            print(f"   - {trava.acao}: EV {aloc.esperanca_estatistica:+.2f}% | Payoff {trava.payoff:.2f}% | Distância {trava.distancia_ativo:.2f}%")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Calcular alocação de capital entre travas')
    parser.add_argument('--capital', type=float, default=1000.0, help='Capital total disponível (padrão: R$ 1000)')
    parser.add_argument('--alpha', type=float, default=1.5, help='Fator alpha heurística (padrão: 1.5)')
    parser.add_argument('--metodo', type=str, default='proporcional', 
                       choices=['proporcional', 'kelly', 'equal_risk'],
                       help='Método de alocação (padrão: proporcional)')
    parser.add_argument('--payoff-min', type=float, default=0.0, 
                       help='Filtrar apenas travas com payoff > X% (padrão: 0 = todas)')
    parser.add_argument('--ev-min', type=float, default=0.0,
                       help='Filtrar apenas travas com EV > X% (padrão: 0 = todas com EV positivo)')
    
    args = parser.parse_args()
    
    # Parse travas
    # Caminho relativo: src/analysis/alocar_travas.py -> mamhedge/radar.md
    script_dir = Path(__file__).parent  # src/analysis
    radar_path = script_dir.parent.parent / "radar.md"  # mamhedge/radar.md
    
    with open(radar_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    parser_trava = TravaParser()
    travas = parser_trava.parse_all_operations(text)
    
    # Filtra por payoff mínimo (se especificado)
    if args.payoff_min > 0:
        travas_filtradas = [t for t in travas if t.payoff >= args.payoff_min]
        print(f"\n📊 Filtrando travas com payoff >= {args.payoff_min}%")
    else:
        travas_filtradas = travas
        print(f"\n📊 Considerando TODAS as {len(travas)} travas (sem filtro de payoff)")
    
    if not travas_filtradas:
        if args.payoff_min > 0:
            print(f"\n❌ Nenhuma trava com payoff >= {args.payoff_min}% encontrada.")
        else:
            print(f"\n❌ Nenhuma trava encontrada.")
        return
    
    print(f"   Encontradas {len(travas_filtradas)} travas")
    
    # Calcula alocações
    print(f"\n🔢 Calculando alocações baseadas em ESPERANÇA ESTATÍSTICA...")
    print(f"   Capital Total: {formatar_moeda(args.capital)}")
    print(f"   Alpha Heurística: {args.alpha}")
    print(f"   Método: {args.metodo}")
    print(f"   💡 Alocação será proporcional ao EV, não apenas ao Payoff")
    
    alocacoes = calcular_alocacao_travas(
        travas_filtradas,
        args.capital,
        alpha_heuristica=args.alpha,
        metodo=args.metodo
    )
    
    # Filtra por EV mínimo se especificado
    if args.ev_min > 0:
        alocacoes = [a for a in alocacoes if a.esperanca_estatistica >= args.ev_min]
        print(f"   Filtrando travas com EV >= {args.ev_min}%")
    
    # Mostra resultados
    mostrar_alocacoes(alocacoes, args.capital)


if __name__ == "__main__":
    main()

