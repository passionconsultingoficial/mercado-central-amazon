import sqlite3
import json
from datetime import datetime

DB_NAME = "marketplace.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asin TEXT NOT NULL,
            data_analise TEXT NOT NULL,
            preco_buy_box REAL,
            custo_unitario REAL,
            margem_alvo REAL,
            regime_tributario TEXT,
            resultado_json TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def salvar_analise(asin, preco_buy_box, custo_unitario, margem_alvo, regime_tributario, resultado_dict):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    resultado_json = json.dumps(resultado_dict, ensure_ascii=False)
    
    cursor.execute('''
        INSERT INTO analises (asin, data_analise, preco_buy_box, custo_unitario, margem_alvo, regime_tributario, resultado_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (asin, data_atual, preco_buy_box, custo_unitario, margem_alvo, regime_tributario, resultado_json))
    
    conn.commit()
    conn.close()

def listar_historico_asin(asin):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, data_analise, preco_buy_box, custo_unitario, regime_tributario 
        FROM analises 
        WHERE asin = ? 
        ORDER BY id DESC
    ''', (asin,))
    
    registros = cursor.fetchall()
    conn.close()
    return registros

def buscar_analise_por_id(analise_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT resultado_json FROM analises WHERE id = ?
    ''', (analise_id,))
    
    registro = cursor.fetchone()
    conn.close()
    
    if registro and registro[0]:
        return json.loads(registro[0])
    return None

if __name__ == "__main__":
    init_db()
    print("Banco de dados atualizado com sucesso!")