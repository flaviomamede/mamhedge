"""
Script interativo para marcar operações como investidas.

Uso:
    python marcar_investimento.py
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.data.storage import (
    OperationDatabase,
    OperationStatus,
    AccountType,
    ConsensoLevel,
    ConfiancaLevel
)


def listar_operacoes_sugeridas(db: OperationDatabase):
    """Lista operações sugeridas disponíveis."""
    operacoes = db.list_operations(status=OperationStatus.SUGERIDA)
    
    if not operacoes:
        print("\n❌ Nenhuma operação sugerida encontrada.")
        return []
    
    print("\n" + "=" * 80)
    print("OPERAÇÕES SUGERIDAS DISPONÍVEIS")
    print("=" * 80)
    
    for i, op in enumerate(operacoes, 1):
        terf = op.operacao_terf
        print(f"\n{i}. ID: {op.id[:8]}...")
        print(f"   Ação: {terf.acao} @ R$ {terf.preco_acao:.2f}")
        print(f"   Call: {terf.codigo_call} (Strike R$ {terf.strike_call:.2f})")
        print(f"   Put: {terf.codigo_put} (Strike R$ {terf.strike_put:.2f})")
        print(f"   Rating: {terf.rating} | CDI: {terf.cdi_periodo:.2f}%")
        print(f"   Rentabilidade: Miolo {terf.rentabilidade_miolo:.2f}% | "
              f"Cima {terf.rentabilidade_cima:.2f}% | "
              f"Baixo {terf.rentabilidade_baixo:.2f}%")
    
    return operacoes


def marcar_investimento_interativo():
    """Interface interativa para marcar investimentos."""
    db = OperationDatabase("mamhedge_operations.db")
    
    # Lista operações sugeridas
    operacoes = listar_operacoes_sugeridas(db)
    
    if not operacoes:
        return
    
    # Seleciona operação
    print("\n" + "=" * 80)
    try:
        escolha = int(input("Escolha o número da operação (ou 0 para cancelar): "))
        if escolha == 0 or escolha > len(operacoes):
            print("Operação cancelada.")
            return
        
        op = operacoes[escolha - 1]
    except (ValueError, KeyboardInterrupt):
        print("\nOperação cancelada.")
        return
    
    # Mostra detalhes da operação
    terf = op.operacao_terf
    print("\n" + "=" * 80)
    print(f"OPERAÇÃO SELECIONADA: {terf.acao}")
    print("=" * 80)
    print(f"Call: {terf.codigo_call} - Strike R$ {terf.strike_call:.2f}")
    print(f"Put: {terf.codigo_put} - Strike R$ {terf.strike_put:.2f}")
    print(f"Coeficiente: R$ {terf.coeficiente:.2f}")
    print(f"Rating: {terf.rating}")
    
    # Pergunta sobre consenso
    print("\n--- Análise de Consenso ---")
    print("1. Forte (3+ carteiras recomendam)")
    print("2. Médio (1-2 carteiras recomendam)")
    print("3. Nulo (Nenhuma carteira menciona)")
    print("4. Contra (Carteiras recomendam venda)")
    
    try:
        consenso_escolha = input("\nNível de consenso (1-4): ").strip()
        consenso_map = {
            '1': ConsensoLevel.FORTE,
            '2': ConsensoLevel.MEDIO,
            '3': ConsensoLevel.NULO,
            '4': ConsensoLevel.CONTRA
        }
        op.consenso = consenso_map.get(consenso_escolha, ConsensoLevel.MEDIO)
    except KeyboardInterrupt:
        print("\nOperação cancelada.")
        return
    
    # Pergunta sobre confiança
    print("\n--- Confiança Ajustada ---")
    print("1. Alta")
    print("2. Média")
    print("3. Baixa")
    
    try:
        confianca_escolha = input("Confiança ajustada (1-3): ").strip()
        confianca_map = {
            '1': ConfiancaLevel.ALTA,
            '2': ConfiancaLevel.MEDIA,
            '3': ConfiancaLevel.BAIXA
        }
        op.confianca_ajustada = confianca_map.get(confianca_escolha, ConfiancaLevel.MEDIA)
    except KeyboardInterrupt:
        print("\nOperação cancelada.")
        return
    
    # Decisão de investimento
    print("\n--- Decisão de Investimento ---")
    print("1. Investir em CONTA REAL")
    print("2. Investir em CONTA SIMULADA")
    print("3. DESCARTAR (não investir)")
    
    try:
        decisao = input("\nSua decisão (1-3): ").strip()
        
        if decisao == '1':
            motivo = input("Motivo da decisão (Enter para pular): ").strip() or None
            op.marcar_investida(AccountType.REAL, motivo)
            print(f"\n✅ Operação marcada como INVESTIDA EM CONTA REAL")
            
        elif decisao == '2':
            motivo = input("Motivo da decisão (Enter para pular): ").strip() or None
            op.marcar_investida(AccountType.SIMULADA, motivo)
            print(f"\n✅ Operação marcada como INVESTIDA EM CONTA SIMULADA")
            
        elif decisao == '3':
            motivo = input("Motivo para descartar (Enter para pular): ").strip() or None
            op.marcar_descartada(motivo)
            print(f"\n✅ Operação marcada como DESCARTADA")
        else:
            print("\n❌ Opção inválida. Operação não alterada.")
            return
        
        # Salva no banco
        db.save_operation(op)
        print(f"💾 Operação salva no banco de dados.")
        
    except KeyboardInterrupt:
        print("\nOperação cancelada.")


if __name__ == "__main__":
    print("=" * 80)
    print("MARCADOR DE INVESTIMENTOS - MamHedge")
    print("=" * 80)
    marcar_investimento_interativo()

