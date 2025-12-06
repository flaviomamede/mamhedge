"""
Exemplo de uso do sistema de armazenamento e registro de operações.

Este script demonstra como:
1. Parsear operações do robô EverHedge
2. Registrar operações no banco de dados
3. Marcar operações como investidas (real ou simulada)
4. Consultar operações registradas
"""

from pathlib import Path
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.data.parsers import EverHedgeParser
from src.data.storage import (
    RegisteredOperation,
    OperationDatabase,
    OperationStatus,
    AccountType,
    ConsensoLevel,
    ConfiancaLevel
)


def exemplo_parsear_e_registrar():
    """Exemplo: Parsear operações e registrar no banco."""
    
    # 1. Parsear operações do robô
    print("=== 1. Parseando operações do robô ===")
    radar_path = Path(__file__).parent.parent.parent.parent / "radar.md"
    
    with open(radar_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    parser = EverHedgeParser()
    terf_operations = parser.parse_all_operations(text)
    
    print(f"Encontradas {len(terf_operations)} operações TERF\n")
    
    # 2. Criar banco de dados
    print("=== 2. Criando banco de dados ===")
    db = OperationDatabase("mamhedge_operations.db")
    
    # 3. Registrar operações
    print("=== 3. Registrando operações ===")
    registered_ops = []
    
    for terf_op in terf_operations:
        # Cria RegisteredOperation a partir da TERFOperation
        reg_op = RegisteredOperation.from_terf_operation(terf_op)
        registered_ops.append(reg_op)
        
        # Salva no banco
        db.save_operation(reg_op)
        
        print(f"  Registrada: {reg_op.id[:8]}... - {reg_op.operacao_terf.acao} - Status: {reg_op.status.value}")
    
    return registered_ops


def exemplo_marcar_investimento():
    """Exemplo: Marcar operações como investidas."""
    
    print("\n=== 4. Marcando operações como investidas ===")
    db = OperationDatabase("mamhedge_operations.db")
    
    # Lista operações sugeridas
    sugeridas = db.list_operations(status=OperationStatus.SUGERIDA)
    
    if not sugeridas:
        print("  Nenhuma operação sugerida encontrada.")
        return
    
    # Exemplo: Marcar primeira como investida em conta simulada
    op1 = sugeridas[0]
    print(f"\n  Operação 1: {op1.operacao_terf.acao} - Rating: {op1.operacao_terf.rating}")
    print(f"    Rentabilidade Miolo: {op1.operacao_terf.rentabilidade_miolo:.2f}%")
    
    # Simula análise de consenso (exemplo)
    # Na prática, você consultaria os relatórios aqui
    consenso = ConsensoLevel.MEDIO  # Exemplo
    confianca = ConfiancaLevel.MEDIA  # Exemplo
    
    op1.consenso = consenso
    op1.confianca_ajustada = confianca
    
    # Decisão: conta simulada (porque consenso é médio)
    if consenso == ConsensoLevel.FORTE:
        op1.marcar_investida(AccountType.REAL, "Consenso forte - 3+ carteiras recomendam")
    else:
        op1.marcar_investida(AccountType.SIMULADA, f"Consenso {consenso.value} - testando em simulada")
    
    db.save_operation(op1)
    print(f"    ✓ Marcada como investida em conta {op1.conta_tipo.value}")
    
    # Exemplo: Marcar segunda como descartada
    if len(sugeridas) > 1:
        op2 = sugeridas[1]
        print(f"\n  Operação 2: {op2.operacao_terf.acao} - Rating: {op2.operacao_terf.rating}")
        op2.marcar_descartada("Rating baixo ou consenso contra")
        db.save_operation(op2)
        print(f"    ✓ Marcada como descartada")


def exemplo_consultar_operacoes():
    """Exemplo: Consultar operações registradas."""
    
    print("\n=== 5. Consultando operações ===")
    db = OperationDatabase("mamhedge_operations.db")
    
    # Todas as operações
    todas = db.list_operations()
    print(f"\n  Total de operações: {len(todas)}")
    
    # Operações investidas em conta real
    reais = db.list_operations(
        status=OperationStatus.INVESTIDA_REAL
    )
    print(f"  Investidas em conta real: {len(reais)}")
    
    # Operações investidas em conta simulada
    simuladas = db.list_operations(
        status=OperationStatus.INVESTIDA_SIMULADA
    )
    print(f"  Investidas em conta simulada: {len(simuladas)}")
    
    # Operações descartadas
    descartadas = db.list_operations(
        status=OperationStatus.DESCARTADA
    )
    print(f"  Descartadas: {len(descartadas)}")
    
    # Mostra detalhes das operações investidas
    if simuladas:
        print("\n  Detalhes das operações simuladas:")
        for op in simuladas[:3]:  # Mostra até 3
            terf = op.operacao_terf
            print(f"    - {terf.acao}: Rating {terf.rating}, "
                  f"Rent. Miolo {terf.rentabilidade_miolo:.2f}%, "
                  f"CDI {terf.cdi_periodo:.2f}%")


if __name__ == "__main__":
    print("=" * 60)
    print("EXEMPLO DE USO DO SISTEMA DE ARMAZENAMENTO")
    print("=" * 60)
    
    # 1. Parsear e registrar
    registered_ops = exemplo_parsear_e_registrar()
    
    # 2. Marcar investimentos
    exemplo_marcar_investimento()
    
    # 3. Consultar
    exemplo_consultar_operacoes()
    
    print("\n" + "=" * 60)
    print("Exemplo concluído!")
    print("Banco de dados criado: mamhedge_operations.db")
    print("=" * 60)

