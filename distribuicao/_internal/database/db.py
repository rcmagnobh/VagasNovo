"""Módulo de acesso ao banco de dados SQLite local."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime

from runtime_paths import get_db_path

DB_PATH = get_db_path()

STATUS_VALIDOS = ("Pendente", "Interessado", "Candidatado", "Entrevista", "Proposta", "Rejeitado")


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS parametros (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                usuario TEXT,
                senha TEXT,
                smtp_servidor TEXT DEFAULT 'smtp.gmail.com',
                smtp_porta INTEGER DEFAULT 587,
                pop_servidor TEXT,
                pop_porta INTEGER DEFAULT 995,
                data_inicio_busca TEXT,
                data_fim_busca TEXT
            );

            CREATE TABLE IF NOT EXISTS palavras_chave (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                termo TEXT NOT NULL UNIQUE,
                ativo INTEGER DEFAULT 1,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS vagas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                empresa TEXT,
                localizacao TEXT,
                link TEXT NOT NULL UNIQUE,
                descricao TEXT,
                data_publicacao TEXT,
                data_captura TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'Pendente',
                obs TEXT,
                palavra_chave TEXT
            );

            CREATE TABLE IF NOT EXISTS historico_buscas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_execucao TEXT DEFAULT CURRENT_TIMESTAMP,
                palavra_chave TEXT,
                vagas_encontradas INTEGER DEFAULT 0,
                vagas_novas INTEGER DEFAULT 0,
                mensagem TEXT
            );
        """)
        conn.execute(
            "INSERT OR IGNORE INTO parametros (id, smtp_porta, pop_porta) VALUES (1, 587, 995)"
        )
        colunas = {row[1] for row in conn.execute("PRAGMA table_info(vagas)").fetchall()}
        novas_colunas = {
            "fonte": "TEXT",
            "cargo": "TEXT",
            "score": "INTEGER",
            "cidade": "TEXT",
            "estado": "TEXT",
            "pais": "TEXT",
            "tipo_vaga": "TEXT",
            "dias_postado": "INTEGER",
        }
        for nome, tipo in novas_colunas.items():
            if nome not in colunas:
                conn.execute(f"ALTER TABLE vagas ADD COLUMN {nome} {tipo}")
        conn.execute(
            "UPDATE vagas SET cargo = titulo WHERE cargo IS NULL OR cargo = ''"
        )
        param_cols = {row[1] for row in conn.execute("PRAGMA table_info(parametros)").fetchall()}
        if "data_inicio_busca" not in param_cols:
            conn.execute("ALTER TABLE parametros ADD COLUMN data_inicio_busca TEXT")
        if "data_fim_busca" not in param_cols:
            conn.execute("ALTER TABLE parametros ADD COLUMN data_fim_busca TEXT")


def get_parametros():
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM parametros WHERE id = 1").fetchone()
        return dict(row) if row else {}


def salvar_parametros(usuario, senha, smtp_servidor, smtp_porta, pop_servidor, pop_porta,
                       data_inicio_busca=None, data_fim_busca=None):
    with get_connection() as conn:
        conn.execute(
            """UPDATE parametros SET usuario=?, senha=?, smtp_servidor=?,
               smtp_porta=?, pop_servidor=?, pop_porta=?,
               data_inicio_busca=?, data_fim_busca=? WHERE id=1""",
            (usuario, senha, smtp_servidor, smtp_porta, pop_servidor, pop_porta,
             data_inicio_busca, data_fim_busca),
        )


def salvar_intervalo_busca(data_inicio, data_fim):
    with get_connection() as conn:
        conn.execute(
            "UPDATE parametros SET data_inicio_busca=?, data_fim_busca=? WHERE id=1",
            (data_inicio, data_fim),
        )


def get_intervalo_busca():
    params = get_parametros()
    return params.get("data_inicio_busca"), params.get("data_fim_busca")


def zerar_banco():
    """Remove vagas, histórico e palavras-chave. Mantém parâmetros de e-mail."""
    with get_connection() as conn:
        conn.execute("DELETE FROM vagas")
        conn.execute("DELETE FROM historico_buscas")
        conn.execute("DELETE FROM palavras_chave")


def listar_palavras_chave(apenas_ativas=False):
    query = "SELECT * FROM palavras_chave"
    if apenas_ativas:
        query += " WHERE ativo = 1"
    query += " ORDER BY termo"
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(query).fetchall()]


def adicionar_palavra_chave(termo):
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO palavras_chave (termo) VALUES (?)", (termo.strip(),))


def remover_palavra_chave(termo_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM palavras_chave WHERE id = ?", (termo_id,))


def toggle_palavra_chave(termo_id, ativo):
    with get_connection() as conn:
        conn.execute("UPDATE palavras_chave SET ativo = ? WHERE id = ?", (int(ativo), termo_id))


def inserir_vaga(vaga):
    cargo = vaga.get("cargo") or vaga.get("titulo")
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT OR IGNORE INTO vagas
               (titulo, cargo, empresa, localizacao, cidade, estado, pais,
                link, descricao, data_publicacao, dias_postado, tipo_vaga, score,
                data_captura, status, obs, palavra_chave, fonte)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                cargo,
                cargo,
                vaga.get("empresa"),
                vaga.get("localizacao"),
                vaga.get("cidade"),
                vaga.get("estado"),
                vaga.get("pais"),
                vaga.get("link"),
                vaga.get("descricao"),
                vaga.get("data_publicacao"),
                vaga.get("dias_postado"),
                vaga.get("tipo_vaga"),
                vaga.get("score"),
                vaga.get("data_captura", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                vaga.get("status", "Pendente"),
                vaga.get("obs"),
                vaga.get("palavra_chave"),
                vaga.get("fonte"),
            ),
        )
        return cursor.rowcount


def atualizar_vaga(vaga_id, **campos):
    permitidos = {
        "titulo", "cargo", "empresa", "localizacao", "cidade", "estado", "pais",
        "link", "descricao", "data_publicacao", "dias_postado", "tipo_vaga",
        "score", "status", "obs", "palavra_chave", "fonte",
    }
    if "cargo" in campos and campos["cargo"]:
        campos.setdefault("titulo", campos["cargo"])
    if "titulo" in campos and campos["titulo"] and "cargo" not in campos:
        campos["cargo"] = campos["titulo"]
    updates = {k: v for k, v in campos.items() if k in permitidos and v is not None}
    if not updates:
        return
    cols = ", ".join(f"{k} = ?" for k in updates)
    valores = list(updates.values()) + [vaga_id]
    with get_connection() as conn:
        conn.execute(f"UPDATE vagas SET {cols} WHERE id = ?", valores)


def excluir_vaga(vaga_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM vagas WHERE id = ?", (vaga_id,))


def contar_vagas():
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) as total FROM vagas").fetchone()
        return row["total"] if row else 0


def listar_vagas(filtro_texto=None, status=None, palavra_chave=None, tipo_vaga=None):
    query = "SELECT * FROM vagas WHERE 1=1"
    params = []
    if filtro_texto:
        query += """ AND (
            titulo LIKE ? OR cargo LIKE ? OR empresa LIKE ?
            OR descricao LIKE ? OR obs LIKE ? OR cidade LIKE ? OR estado LIKE ?
        )"""
        termo = f"%{filtro_texto}%"
        params.extend([termo] * 7)
    if status and status != "Todos":
        query += " AND status = ?"
        params.append(status)
    if palavra_chave and palavra_chave != "Todos":
        query += " AND palavra_chave = ?"
        params.append(palavra_chave)
    if tipo_vaga and tipo_vaga != "Todos":
        query += " AND tipo_vaga = ?"
        params.append(tipo_vaga)
    query += " ORDER BY COALESCE(score, 0) DESC, data_captura DESC"
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def get_vaga(vaga_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM vagas WHERE id = ?", (vaga_id,)).fetchone()
        return dict(row) if row else None


def registrar_historico_busca(palavra_chave, encontradas, novas, mensagem=""):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO historico_buscas
               (palavra_chave, vagas_encontradas, vagas_novas, mensagem)
               VALUES (?, ?, ?, ?)""",
            (palavra_chave, encontradas, novas, mensagem),
        )


def listar_historico_buscas(limite=50):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM historico_buscas ORDER BY data_execucao DESC LIMIT ?",
            (limite,),
        ).fetchall()
        return [dict(r) for r in rows]


def contar_vagas_por_status():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as total FROM vagas GROUP BY status"
        ).fetchall()
        return {r["status"]: r["total"] for r in rows}


def contar_vagas_por_palavra_chave():
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT palavra_chave, COUNT(*) as total FROM vagas
               WHERE palavra_chave IS NOT NULL GROUP BY palavra_chave
               ORDER BY total DESC"""
        ).fetchall()
        return {r["palavra_chave"]: r["total"] for r in rows}


def vagas_por_dia(limite_dias=30):
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT DATE(data_captura) as dia, COUNT(*) as total
               FROM vagas GROUP BY DATE(data_captura)
               ORDER BY dia DESC LIMIT ?""",
            (limite_dias,),
        ).fetchall()
        return [(r["dia"], r["total"]) for r in reversed(rows)]
