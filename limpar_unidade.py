# -*- coding: utf-8 -*-
"""Apaga os relatórios de uma unidade no Supabase. Uso: python limpar_unidade.py "Nome" """
import sys
import db as DB

nome = sys.argv[1] if len(sys.argv) > 1 else "Casa de Acolhida"
conn = DB.get_conn(); cur = DB.cur_dict(conn)
r = cur.execute("SELECT id FROM unidades WHERE nome=%s", (nome,)).fetchone()
if not r:
    print(f"⚠️ Unidade '{nome}' não encontrada.")
else:
    n = cur.execute("SELECT COUNT(*) AS n FROM relatorios WHERE unidade_id=%s", (r["id"],)).fetchone()["n"]
    c = conn.cursor()
    c.execute("DELETE FROM relatorios WHERE unidade_id=%s", (r["id"],))
    conn.commit()
    print(f"🗑️ {n} registros de '{nome}' apagados do Supabase.")
conn.close()