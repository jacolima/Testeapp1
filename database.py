import sqlite3
from datetime import datetime

DB_NAME = 'gestor_financeiro.db'

def criar_tabelas():
    """Cria as tabelas no banco de dados se elas não existirem."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabela de categorias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('Receita', 'Despesa'))
        )
    ''')

    # Tabela de transações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('Receita', 'Despesa')),
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            categoria_id INTEGER,
            data_vencimento TEXT,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id)
        )
    ''')
    
    # Tabela de investimentos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS investimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ativo TEXT NOT NULL,
            valor_atual REAL NOT NULL,
            data_atualizacao TEXT NOT NULL
        )
    ''')

    # Tabela de dívidas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dividas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            valor_total REAL NOT NULL,
            valor_pago REAL DEFAULT 0
        )
    ''')

    # Verifica se as categorias padrão já existem
    cursor.execute("SELECT COUNT(*) FROM categorias")
    if cursor.fetchone()[0] == 0:
        categorias_padrao = [
            ('Salário', 'Receita'),
            ('Vale Refeição', 'Receita'),
            ('Freelance', 'Receita'),
            ('Moradia', 'Despesa'),
            ('Transporte', 'Despesa'),
            ('Alimentação', 'Despesa'),
            ('Lazer', 'Despesa'),
            ('Saúde', 'Despesa'),
            ('Educação', 'Despesa')
        ]
        cursor.executemany("INSERT INTO categorias (nome, tipo) VALUES (?, ?)", categorias_padrao)

    conn.commit()
    conn.close()

def formatar_moeda(valor):
    """Formata um valor numérico para o formato de moeda BRL."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- Funções do Dashboard ---
def get_dados_dashboard():
    """Busca os dados agregados para o dashboard."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    mes_atual = datetime.now().strftime('%Y-%m')

    # Saldo do Mês
    cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM transacoes WHERE tipo = 'Receita' AND strftime('%Y-%m', data) = ?", (mes_atual,))
    receitas = cursor.fetchone()[0]
    cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM transacoes WHERE tipo = 'Despesa' AND strftime('%Y-%m', data) = ?", (mes_atual,))
    despesas = cursor.fetchone()[0]
    saldo = receitas - despesas

    # Total Investido
    cursor.execute("SELECT COALESCE(SUM(valor_atual), 0) FROM investimentos")
    investimentos = cursor.fetchone()[0]

    # Dívidas Pendentes
    cursor.execute("SELECT COALESCE(SUM(valor_total - valor_pago), 0) FROM dividas")
    dividas = cursor.fetchone()[0]

    # Dados para o gráfico
    cursor.execute("""
        SELECT c.nome, SUM(t.valor)
        FROM transacoes t
        JOIN categorias c ON t.categoria_id = c.id
        WHERE t.tipo = 'Despesa' AND strftime('%Y-%m', t.data) = ?
        GROUP BY c.nome
    """, (mes_atual,))
    chart_data_raw = cursor.fetchall()
    
    chart_data = {
        'labels': [row[0] for row in chart_data_raw],
        'data': [row[1] for row in chart_data_raw]
    }

    conn.close()

    return {
        "saldo": formatar_moeda(saldo),
        "investimentos": formatar_moeda(investimentos),
        "dividas": formatar_moeda(dividas),
        "chart_data": chart_data
    }

# --- Funções de Transações e Categorias ---
def get_categorias(tipo):
    """Busca categorias de um tipo específico (Receita ou Despesa)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM categorias WHERE tipo = ?", (tipo,))
    categorias = cursor.fetchall()
    conn.close()
    return categorias

def inserir_transacao(tipo, descricao, valor, categoria_id, data_vencimento=None):
    """Insere uma nova transação no banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    try:
        cursor.execute("""
            INSERT INTO transacoes (data, tipo, descricao, valor, categoria_id, data_vencimento)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data_hoje, tipo, descricao, float(valor), int(categoria_id), data_vencimento))
        conn.commit()
        return True, "Transação salva com sucesso!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_transacoes(tipo_filtro=None):
    """Busca transações, com filtro opcional por tipo, para a página de extrato."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = """
        SELECT t.id, t.data, t.descricao, t.valor, t.tipo, c.nome
        FROM transacoes t
        LEFT JOIN categorias c ON t.categoria_id = c.id
    """
    params = []

    if tipo_filtro in ['Receita', 'Despesa']:
        query += " WHERE t.tipo = ?"
        params.append(tipo_filtro)

    query += " ORDER BY t.data DESC, t.id DESC"

    cursor.execute(query, params)
    transacoes = cursor.fetchall()
    conn.close()
    return transacoes

# --- Funções de Dívidas ---
def get_dividas():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, descricao, valor_total, valor_pago FROM dividas ORDER BY id DESC")
    dividas = cursor.fetchall()
    conn.close()
    return dividas

def inserir_divida(descricao, valor_total):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO dividas (descricao, valor_total) VALUES (?, ?)", (descricao, float(valor_total)))
        conn.commit()
        return True, "Dívida adicionada!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def remover_divida(divida_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM dividas WHERE id = ?", (divida_id,))
        conn.commit()
        return True, "Dívida removida!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# --- Funções de Investimentos ---
def get_investimentos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, ativo, valor_atual, data_atualizacao FROM investimentos ORDER BY id DESC")
    investimentos = cursor.fetchall()
    conn.close()
    return investimentos

def inserir_investimento(ativo, valor_atual):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    try:
        cursor.execute("INSERT INTO investimentos (ativo, valor_atual, data_atualizacao) VALUES (?, ?, ?)", (ativo, float(valor_atual), data_hoje))
        conn.commit()
        return True, "Investimento adicionado!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def remover_investimento(investimento_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM investimentos WHERE id = ?", (investimento_id,))
        conn.commit()
        return True, "Investimento removido!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()