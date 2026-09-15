# -*- coding: utf-8 -*-
"""Auditoria do banco (Supabase)."""
import json
from collections import defaultdict
import db as DB

conn = DB.get_conn(); cur = DB.cur_dict(conn)
rows = cur.execute("""SELECT u.nome, u.tipo, r.mes, r.ano, r.dados
                      FROM relatorios r JOIN unidades u ON u.id=r.unidade_id
                      ORDER BY u.nome, r.ano, r.mes""").fetchall()
conn.close()

print(f"📊 TOTAL DE REGISTROS NO BANCO: {len(rows)}\n")
por = defaultdict(list)
for r in rows:
    por[(r["nome"], r["tipo"])].append(r["mes"])
for (nome, tipo) in sorted(por):
    print(f"   ✅ {nome:<35} [{tipo}] meses: {sorted(por[(nome, tipo)])}")

if rows:
    d = json.loads(rows[0]["dados"]) if rows[0]["dados"] else {}
    print(f"\n🔎 AMOSTRA — {rows[0]['nome']}, mês {rows[0]['mes']}: {len(d)} campos")
    for k, v in list(d.items())[:6]:
        print(f"      {k} = {v}")
print("\n✅ Auditoria concluída.")