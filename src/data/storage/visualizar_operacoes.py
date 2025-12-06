"""
Script para visualizar operações registradas.

Uso:
    python visualizar_operacoes.py [--status STATUS] [--conta TIPO]
    
Exemplos:
    python visualizar_operacoes.py
    python visualizar_operacoes.py --status investida_real
    python visualizar_operacoes.py --status investida_simulada
    python visualizar_operacoes.py --status descartada
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.data.storage import (
    OperationDatabase,
    OperationStatus,
    AccountType
)


def formatar_data(data: datetime) -> str:
    """Formata data para exibição."""
    if not data:
        return "N/A"
    return data.strftime("%d/%m/%Y %H:%M")


def visualizar_operacao(op, detalhes: bool = False):
    """Formata e exibe uma operação."""
    terf = op.operacao_terf
    
    print("\n" + "=" * 80)
    print(f"ID: {op.id}")
    print(f"Status: {op.status.value.upper()}")
    if op.conta_tipo:
        print(f"Conta: {op.conta_tipo.value.upper()}")
    print("=" * 80)
    
    print(f"\n📊 OPERAÇÃO:")
    print(f"   Ação: {terf.acao} @ R$ {terf.preco_acao:.2f}")
    print(f"   Call: {terf.codigo_call} - Strike R$ {terf.strike_call:.2f} - Venc: {terf.vencimento_call.strftime('%d/%m/%Y')}")
    print(f"   Put: {terf.codigo_put} - Strike R$ {terf.strike_put:.2f} - Venc: {terf.vencimento_put.strftime('%d/%m/%Y')}")
    print(f"   Coeficiente: R$ {terf.coeficiente:.2f}")
    print(f"   Rating: {terf.rating}")
    
    print(f"\n💰 RENTABILIDADES:")
    print(f"   Miolo: {terf.rentabilidade_miolo:.2f}%")
    print(f"   Cima: {terf.rentabilidade_cima:.2f}%")
    print(f"   Baixo: {terf.rentabilidade_baixo:.2f}%")
    print(f"   CDI Período: {terf.cdi_periodo:.2f}%")
    
    if detalhes:
        print(f"\n📈 ANÁLISE:")
        if op.consenso:
            print(f"   Consenso: {op.consenso.value}")
        if op.confianca_ajustada:
            print(f"   Confiança Ajustada: {op.confianca_ajustada.value}")
        if op.probabilidade_app:
            print(f"   Probabilidade App: {op.probabilidade_app:.1f}%")
        
        print(f"\n💼 EXECUÇÃO:")
        if op.data_decisao:
            print(f"   Data Decisão: {formatar_data(op.data_decisao)}")
        if op.motivo_decisao:
            print(f"   Motivo: {op.motivo_decisao}")
        if op.custo_montagem:
            print(f"   Custo Montagem: R$ {op.custo_montagem:.2f}")
        if op.alvo_saida:
            print(f"   Alvo Saída: R$ {op.alvo_saida:.2f}")
        if op.preco_atual:
            print(f"   Preço Atual: R$ {op.preco_atual:.2f}")
        if op.resultado_atual_pct is not None:
            print(f"   Resultado Atual: {op.resultado_atual_pct:.2f}%")
        
        print(f"\n✅ VALIDAÇÃO:")
        if op.data_saida:
            print(f"   Data Saída: {formatar_data(op.data_saida)}")
        if op.lucro_prejuizo_real is not None:
            sinal = "+" if op.lucro_prejuizo_real >= 0 else ""
            print(f"   Lucro/Prejuízo: {sinal}R$ {op.lucro_prejuizo_real:.2f}")
        if op.status_final:
            print(f"   Status Final: {op.status_final}")
        if op.bayes_confirmou is not None:
            print(f"   Bayes Confirmou: {'Sim' if op.bayes_confirmou else 'Não'}")
        
        print(f"\n📝 METADADOS:")
        print(f"   Registrado em: {formatar_data(op.data_registro)}")
        print(f"   Atualizado em: {formatar_data(op.data_atualizacao)}")
        if op.notas:
            print(f"   Notas: {op.notas}")


def visualizar_resumo(db: OperationDatabase):
    """Mostra resumo geral das operações."""
    todas = db.list_operations()
    
    print("\n" + "=" * 80)
    print("RESUMO GERAL")
    print("=" * 80)
    
    status_count = {}
    for op in todas:
        status = op.status.value
        status_count[status] = status_count.get(status, 0) + 1
    
    print(f"\nTotal de operações: {len(todas)}")
    print("\nPor Status:")
    for status, count in sorted(status_count.items()):
        print(f"   {status}: {count}")
    
    # Investidas
    reais = db.list_operations(status=OperationStatus.INVESTIDA_REAL)
    simuladas = db.list_operations(status=OperationStatus.INVESTIDA_SIMULADA)
    
    if reais or simuladas:
        print(f"\n💰 INVESTIDAS:")
        if reais:
            print(f"   Conta Real: {len(reais)}")
        if simuladas:
            print(f"   Conta Simulada: {len(simuladas)}")


def main():
    parser = argparse.ArgumentParser(description='Visualizar operações registradas')
    parser.add_argument('--status', type=str, help='Filtrar por status (sugerida, investida_real, investida_simulada, descartada, encerrada)')
    parser.add_argument('--conta', type=str, help='Filtrar por tipo de conta (real, simulada)')
    parser.add_argument('--detalhes', action='store_true', help='Mostrar detalhes completos')
    parser.add_argument('--resumo', action='store_true', help='Mostrar apenas resumo')
    parser.add_argument('--id', type=str, help='Mostrar operação específica por ID')
    
    args = parser.parse_args()
    
    db = OperationDatabase("mamhedge_operations.db")
    
    # Resumo
    if args.resumo:
        visualizar_resumo(db)
        return
    
    # Operação específica
    if args.id:
        op = db.get_operation(args.id)
        if op:
            visualizar_operacao(op, detalhes=True)
        else:
            print(f"❌ Operação com ID {args.id} não encontrada.")
        return
    
    # Filtros
    status = None
    if args.status:
        status_map = {
            'sugerida': OperationStatus.SUGERIDA,
            'investida_real': OperationStatus.INVESTIDA_REAL,
            'investida_simulada': OperationStatus.INVESTIDA_SIMULADA,
            'descartada': OperationStatus.DESCARTADA,
            'encerrada': OperationStatus.ENCERRADA
        }
        status = status_map.get(args.status.lower())
    
    conta_tipo = None
    if args.conta:
        conta_map = {
            'real': AccountType.REAL,
            'simulada': AccountType.SIMULADA
        }
        conta_tipo = conta_map.get(args.conta.lower())
    
    # Lista operações
    operacoes = db.list_operations(status=status, conta_tipo=conta_tipo)
    
    if not operacoes:
        print("\n❌ Nenhuma operação encontrada com os filtros especificados.")
        return
    
    print(f"\n📋 Encontradas {len(operacoes)} operação(ões)\n")
    
    for op in operacoes:
        visualizar_operacao(op, detalhes=args.detalhes)


if __name__ == "__main__":
    main()

