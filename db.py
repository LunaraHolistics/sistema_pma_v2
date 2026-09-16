# -*- coding: utf-8 -*-
"""Camada de acesso ao Supabase (Postgres) + utilitários de backup."""
import os, sqlite3, json, tempfile
import datetime as _dt
import decimal as _dec
import psycopg2
from psycopg2.extras import RealDictCursor

try:
    from config_local import DATABASE_URL        # uso local (NÃO vai p/ GitHub)
except ImportError:
    DATABASE_URL = os.environ.get("DATABASE_URL", "")   # Render

TABELAS_COLS = {
    "unidades": ["id","nome","tipo"],
    "usuarios": ["id","email","papel","unidade_id","origem","criado_em"],
    "usuario_unidades": ["id","user_id","unidade_id"],
    "campos_config": ["id","tipo","chave","rotulo","secao","ativo","vigente_mes","vigente_ano","origem","criado_em"],
    "relatorios": ["id","unidade_id","tipo","mes","ano","email_usuario","data_envio","dados"],
    "filtros_salvos": ["id","email_usuario","nome_filtro","tipo_relatorio","parametros","data_criacao"],
}

SQLITE_SCHEMA = """
CREATE TABLE unidades (id INTEGER PRIMARY KEY, nome TEXT, tipo TEXT);
CREATE TABLE usuarios (id INTEGER PRIMARY KEY, email TEXT, papel TEXT, unidade_id INTEGER, origem TEXT, criado_em TEXT);
CREATE TABLE usuario_unidades (id INTEGER PRIMARY KEY, user_id INTEGER, unidade_id INTEGER);
CREATE TABLE campos_config (id INTEGER PRIMARY KEY, tipo TEXT, chave TEXT, rotulo TEXT, secao TEXT, ativo INTEGER, vigente_mes INTEGER, vigente_ano INTEGER, origem TEXT, criado_em TEXT);
CREATE TABLE relatorios (id INTEGER PRIMARY KEY, unidade_id INTEGER, tipo TEXT, mes INTEGER, ano INTEGER, email_usuario TEXT, data_envio TEXT, dados TEXT);
CREATE TABLE filtros_salvos (id INTEGER PRIMARY KEY, email_usuario TEXT, nome_filtro TEXT, tipo_relatorio TEXT, parametros TEXT, data_criacao TEXT);
"""

def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não configurada (config_local.py ou variável de ambiente).")
    return psycopg2.connect(DATABASE_URL)

def cur_dict(conn):
    return conn.cursor(cursor_factory=RealDictCursor)

def _sqlite_safe(v):
    """Converte tipos do Postgres para tipos que o SQLite aceita."""
    if isinstance(v, _dt.datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, (_dt.date, _dt.time)):
        return v.isoformat()
    if isinstance(v, _dec.Decimal):
        return float(v)
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return v

def unidade_id(conn, nome, tipo):
    cur = cur_dict(conn)
    cur.execute("INSERT INTO unidades (nome, tipo) VALUES (%s,%s) ON CONFLICT (nome,tipo) DO NOTHING RETURNING id", (nome, tipo))
    r = cur.fetchone()
    if r: return r["id"]
    cur.execute("SELECT id FROM unidades WHERE nome=%s AND tipo=%s", (nome, tipo))
    return cur.fetchone()["id"]

def upsert_relatorio(conn, unidade_nome, tipo, mes, ano, email, dados_json):
    uid = unidade_id(conn, unidade_nome, tipo)
    cur = conn.cursor()
    cur.execute("""INSERT INTO relatorios (unidade_id, tipo, mes, ano, email_usuario, dados)
                   VALUES (%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (unidade_id, mes, ano)
                   DO UPDATE SET dados=EXCLUDED.dados, email_usuario=EXCLUDED.email_usuario, data_envio=CURRENT_TIMESTAMP""",
                (uid, tipo, mes, ano, email, dados_json))
    conn.commit()
    return uid

def exportar_sqlite_bytes():
    """Gera um snapshot .db (SQLite) com todo o conteúdo do Supabase (botão ⬇️ Backup)."""
    fd, tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        sq = sqlite3.connect(tmp)
        sq.executescript(SQLITE_SCHEMA)
        conn = get_conn(); cur = cur_dict(conn)
        for t, cols in TABELAS_COLS.items():
            cur.execute(f"SELECT {', '.join(cols)} FROM {t}")
            for r in cur.fetchall():
                sq.execute(f"INSERT INTO {t} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                           [_sqlite_safe(r[c]) for c in cols])
        sq.commit(); sq.close(); conn.close()
        with open(tmp, "rb") as f:
            data = f.read()
    finally:
        if os.path.exists(tmp): os.remove(tmp)
    return data

def importar_sqlite_bytes(content: bytes):
    """Substitui todo o conteúdo do Supabase pelo .db enviado (botão ⬆️ Restaurar)."""
    fd, tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    ok = False
    try:
        with open(tmp, "wb") as f:
            f.write(content)
        sq = sqlite3.connect(tmp)
        tabs = [r[0] for r in sq.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        if "relatorios" not in tabs or "unidades" not in tabs:
            return False
        conn = get_conn(); cur = conn.cursor()
        cur.execute("TRUNCATE TABLE unidades, usuarios, usuario_unidades, campos_config, relatorios, filtros_salvos RESTART IDENTITY CASCADE")
        for t, cols in TABELAS_COLS.items():
            if t not in tabs: continue
            info = [r[1] for r in sq.execute(f"PRAGMA table_info({t})")]
            use = [c for c in cols if c in info]
            rows = sq.execute(f"SELECT {', '.join(use)} FROM {t}").fetchall()
            if rows:
                cur.executemany(f"INSERT INTO {t} ({', '.join(use)}) VALUES ({','.join(['%s'] * len(use))})", rows)
        for t in TABELAS_COLS:
            cur.execute(f"SELECT setval(pg_get_serial_sequence('{t}','id'), COALESCE((SELECT MAX(id) FROM {t}),1))")
        conn.commit(); conn.close(); sq.close()
        ok = True
    finally:
        if os.path.exists(tmp): os.remove(tmp)
    return ok