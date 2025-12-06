"""
Sistema de armazenamento de operações.

Usa SQLite para armazenar operações parseadas e decisões de investimento.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from .models import RegisteredOperation, OperationStatus, AccountType


class OperationDatabase:
    """Banco de dados para armazenar operações."""
    
    def __init__(self, db_path: str = "mamhedge_operations.db"):
        """
        Inicializa o banco de dados.
        
        Args:
            db_path: Caminho para o arquivo SQLite
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Cria as tabelas se não existirem."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela principal de operações
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operations (
                id TEXT PRIMARY KEY,
                estrategia TEXT,
                probabilidade_app REAL,
                consenso TEXT,
                confianca_ajustada TEXT,
                status TEXT,
                conta_tipo TEXT,
                data_decisao TEXT,
                motivo_decisao TEXT,
                custo_montagem REAL,
                alvo_saida REAL,
                preco_atual REAL,
                resultado_atual_pct REAL,
                distancia_alvo REAL,
                decisao_hoje TEXT,
                data_saida TEXT,
                lucro_prejuizo_real REAL,
                status_final TEXT,
                bayes_confirmou INTEGER,
                data_registro TEXT,
                data_atualizacao TEXT,
                notas TEXT,
                operacao_terf_json TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_operation(self, operation: RegisteredOperation):
        """Salva ou atualiza uma operação."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Serializa a TERF operation para JSON
        terf_json = json.dumps(operation.operacao_terf.to_dict() if operation.operacao_terf else None)
        
        cursor.execute("""
            INSERT OR REPLACE INTO operations (
                id, estrategia, probabilidade_app, consenso, confianca_ajustada,
                status, conta_tipo, data_decisao, motivo_decisao,
                custo_montagem, alvo_saida, preco_atual, resultado_atual_pct,
                distancia_alvo, decisao_hoje, data_saida, lucro_prejuizo_real,
                status_final, bayes_confirmou, data_registro, data_atualizacao,
                notas, operacao_terf_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            operation.id,
            operation.estrategia,
            operation.probabilidade_app,
            operation.consenso.value if operation.consenso else None,
            operation.confianca_ajustada.value if operation.confianca_ajustada else None,
            operation.status.value,
            operation.conta_tipo.value if operation.conta_tipo else None,
            operation.data_decisao.isoformat() if operation.data_decisao else None,
            operation.motivo_decisao,
            operation.custo_montagem,
            operation.alvo_saida,
            operation.preco_atual,
            operation.resultado_atual_pct,
            operation.distancia_alvo,
            operation.decisao_hoje,
            operation.data_saida.isoformat() if operation.data_saida else None,
            operation.lucro_prejuizo_real,
            operation.status_final,
            operation.bayes_confirmou,
            operation.data_registro.isoformat(),
            operation.data_atualizacao.isoformat(),
            operation.notas,
            terf_json
        ))
        
        conn.commit()
        conn.close()
    
    def get_operation(self, operation_id: str) -> Optional[RegisteredOperation]:
        """Recupera uma operação por ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM operations WHERE id = ?", (operation_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_operation(row)
        return None
    
    def list_operations(
        self,
        status: Optional[OperationStatus] = None,
        conta_tipo: Optional[AccountType] = None,
        limit: Optional[int] = None
    ) -> List[RegisteredOperation]:
        """Lista operações com filtros opcionais."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM operations WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status.value)
        
        if conta_tipo:
            query += " AND conta_tipo = ?"
            params.append(conta_tipo.value)
        
        query += " ORDER BY data_registro DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_operation(row) for row in rows]
    
    def _row_to_operation(self, row: sqlite3.Row) -> RegisteredOperation:
        """Converte uma linha do banco para RegisteredOperation."""
        from ..parsers.everhedge_parser import TERFOperation
        from datetime import datetime
        
        # Deserializa TERF operation
        terf_op = None
        if row['operacao_terf_json']:
            terf_dict = json.loads(row['operacao_terf_json'])
            if terf_dict:
                # Converte datas de string para datetime
                terf_dict['data_busca'] = datetime.fromisoformat(terf_dict['data_busca'])
                terf_dict['vencimento_call'] = datetime.fromisoformat(terf_dict['vencimento_call'])
                terf_dict['vencimento_put'] = datetime.fromisoformat(terf_dict['vencimento_put'])
                terf_op = TERFOperation(**terf_dict)
        
        return RegisteredOperation(
            id=row['id'],
            operacao_terf=terf_op,
            estrategia=row['estrategia'],
            probabilidade_app=row['probabilidade_app'],
            consenso=ConsensoLevel(row['consenso']) if row['consenso'] else None,
            confianca_ajustada=ConfiancaLevel(row['confianca_ajustada']) if row['confianca_ajustada'] else None,
            status=OperationStatus(row['status']),
            conta_tipo=AccountType(row['conta_tipo']) if row['conta_tipo'] else None,
            data_decisao=datetime.fromisoformat(row['data_decisao']) if row['data_decisao'] else None,
            motivo_decisao=row['motivo_decisao'],
            custo_montagem=row['custo_montagem'],
            alvo_saida=row['alvo_saida'],
            preco_atual=row['preco_atual'],
            resultado_atual_pct=row['resultado_atual_pct'],
            distancia_alvo=row['distancia_alvo'],
            decisao_hoje=row['decisao_hoje'],
            data_saida=datetime.fromisoformat(row['data_saida']) if row['data_saida'] else None,
            lucro_prejuizo_real=row['lucro_prejuizo_real'],
            status_final=row['status_final'],
            bayes_confirmou=bool(row['bayes_confirmou']) if row['bayes_confirmou'] is not None else None,
            data_registro=datetime.fromisoformat(row['data_registro']),
            data_atualizacao=datetime.fromisoformat(row['data_atualizacao']),
            notas=row['notas']
        )
    
    def update_operation_status(self, operation_id: str, status: OperationStatus):
        """Atualiza o status de uma operação."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE operations SET status = ?, data_atualizacao = ? WHERE id = ?",
            (status.value, datetime.now().isoformat(), operation_id)
        )
        
        conn.commit()
        conn.close()

