# -*- coding: utf-8 -*-
import json, io, os, re, unicodedata
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from openpyxl import Workbook
import campos, ajustes
import db as DB
import database as _dbmod
from database import USUARIOS_SEED

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "pma_araraquara_2026")

GESTORAS = {e for e, p, _ in USUARIOS_SEED if p == "gestora"}
GESTORAS |= {e.strip().lower() for e in os.environ.get("GESTORAS_EXTRA", "").split(",") if e.strip()}
SEED_EMAILS = {e for e, _, _ in USUARIOS_SEED}
SENHA_PADRAO = os.environ.get("SENHA_PMA", "Pma@123")
TIPOS_ESPECIAIS = ["acolhida", "centro_pop", "centro_dia_idoso",
                   "residencia_inclusiva", "republica_idosos", "promaip"]

_dbmod.init_db()

def db():
    return DB.get_conn()

def eh_gestora():
    return session.get("user", "") in GESTORAS

def minhas_unidades():
    conn = db(); cur = DB.cur_dict(conn)
    cur.execute("""SELECT u.id, u.nome, u.tipo FROM usuario_unidades vu
                  JOIN unidades u ON u.id = vu.unidade_id
                  JOIN usuarios us ON us.id = vu.user_id
                  WHERE us.email = %s ORDER BY u.nome""", (session.get("user"),))
    rows = cur.fetchall()
    conn.close(); return rows

def unidade_atual():
    unids = minhas_unidades()
    if not unids: return None
    cur_id = session.get("unidade_atual")
    for u in unids:
        if u["id"] == cur_id: return u
    return unids[0]

@app.context_processor
def inject_globals():
    return {"eh_gestora": eh_gestora(),
            "tipos_lista": [(t, campos.CAMPOS[t]["nome"]) for t in campos.CAMPOS]}

# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        if senha != SENHA_PADRAO:
            return render_template("login.html", erro="E-mail não autorizado ou senha inválida.")
        conn = db(); cur = DB.cur_dict(conn)
        cur.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
        u = cur.fetchone()
        if u is None and email not in SEED_EMAILS:
            conn.close()
            return render_template("login.html", erro="E-mail não autorizado ou senha inválida.")
        if u is None:
            cur.execute("INSERT INTO usuarios (email, papel, origem) VALUES (%s,%s,'seed') ON CONFLICT (email) DO NOTHING",
                        (email, "gestora" if email in GESTORAS else "equipamento"))
            conn.commit()
            cur.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
            u = cur.fetchone()
        papel = "gestora" if email in GESTORAS else u["papel"]
        cur.execute("UPDATE usuarios SET papel=%s WHERE id=%s", (papel, u["id"]))
        conn.commit(); conn.close()
        session["user"] = email; session["papel"] = papel
        return redirect(url_for("dashboard") if papel == "gestora" else url_for("painel"))
    if session.get("user"):
        return redirect(url_for("dashboard") if eh_gestora() else url_for("painel"))
    return render_template("login.html")

@app.route("/sair")
def sair():
    session.clear(); return redirect(url_for("login"))

# ================= PAINEL DO EQUIPAMENTO =================
@app.route("/painel")
def painel():
    if not session.get("user"): return redirect(url_for("login"))
    if eh_gestora(): return redirect(url_for("dashboard"))
    un = unidade_atual()
    conn = db(); cur = DB.cur_dict(conn)
    if un:
        cur.execute("SELECT * FROM relatorios WHERE unidade_id=%s ORDER BY ano DESC, mes DESC", (un["id"],))
        regs = cur.fetchall()
    else:
        regs = []
    conn.close()
    return render_template("painel_equipamento.html", un=un, unids=minhas_unidades(), regs=regs)

@app.route("/painel/unidade/<int:uid>")
def trocar_unidade(uid):
    if session.get("user") and uid in [u["id"] for u in minhas_unidades()]:
        session["unidade_atual"] = uid
    return redirect(url_for("painel"))

@app.route("/painel/editar", methods=["GET", "POST"])
def editar():
    if not session.get("user") or eh_gestora(): return redirect(url_for("login"))
    un = unidade_atual()
    if not un: return redirect(url_for("painel"))
    tipo = un["tipo"]
    secoes = secoes_do(tipo, None, None)
    mes = int(request.form.get("mes") or request.args.get("mes", 0))
    ano = int(request.form.get("ano") or request.args.get("ano", 2026))
    conn = db(); cur = DB.cur_dict(conn)
    cur.execute("SELECT * FROM relatorios WHERE unidade_id=%s AND mes=%s AND ano=%s", (un["id"], mes, ano))
    reg = cur.fetchone()
    dados = json.loads(reg["dados"]) if reg and reg["dados"] else {}
    if request.method == "POST":
        novo = {}
        for _, lista in secoes:
            for chave, _rot in lista:
                v = (request.form.get(chave) or "").strip()
                if v == "": novo[chave] = None
                else:
                    try: novo[chave] = int(float(v))
                    except: novo[chave] = v
        for k, v in dados.items(): novo.setdefault(k, v)
        DB.upsert_relatorio(conn, un["nome"], tipo, mes, ano, session["user"], json.dumps(novo, ensure_ascii=False))
        conn.close()
        return redirect(url_for("painel"))
    conn.close()
    return render_template("form_equipamento.html", un=un, mes=mes, ano=ano, dados=dados, secoes=secoes)

# ================= IMPRIMIR / MODELO =================
@app.route("/imprimir")
def imprimir():
    if not session.get("user"): return redirect(url_for("login"))
    conn = db(); cur = DB.cur_dict(conn)
    if eh_gestora():
        uid = request.args.get("unidade_id")
        if uid:
            cur.execute("SELECT * FROM unidades WHERE id=%s", (uid,))
            un = cur.fetchone()
        else:
            un = None
    else:
        un = unidade_atual()
    mes, ano = int(request.args.get("mes")), int(request.args.get("ano"))
    cur.execute("SELECT * FROM relatorios WHERE unidade_id=%s AND mes=%s AND ano=%s", (un["id"], mes, ano))
    reg = cur.fetchone()
    dados = json.loads(reg["dados"]) if reg and reg["dados"] else {}
    conn.close()
    secoes = secoes_do(un["tipo"], mes, ano)
    chaves_dna = {k for _, l in secoes for k, _r in l}
    extras = [(k, v) for k, v in dados.items() if k not in chaves_dna and v not in (None, "")]
    return render_template("relatorio_imprimir.html", un=un, mes=mes, ano=ano, dados=dados, secoes=secoes, extras=extras)

@app.route("/modelo")
def modelo():
    if not session.get("user"): return redirect(url_for("login"))
    tipo = request.args.get("tipo")
    if not tipo: return redirect(url_for("gestao_campos") if eh_gestora() else url_for("painel"))
    if not eh_gestora():
        meus_tipos = {u["tipo"] for u in minhas_unidades()}
        if tipo not in meus_tipos: return "sem permissão", 403
    return render_template("modelo_relatorio.html", tipo=tipo,
                           nome_tipo=campos.CAMPOS[tipo]["nome"], secoes=secoes_do(tipo))

# ================= GESTÃO DE CAMPOS =================
@app.route("/gestao/campos")
def gestao_campos():
    if not eh_gestora(): return redirect(url_for("dashboard"))
    tipo = request.args.get("tipo", "cras")
    conn = db(); cur = DB.cur_dict(conn)
    cur.execute("SELECT * FROM campos_config WHERE tipo=%s ORDER BY id", (tipo,))
    rows = cur.fetchall()
    conn.close()
    return render_template("gestao_campos.html", tipo=tipo, rows=rows)

@app.route("/gestao/campos", methods=["POST"])
def gestao_campos_post():
    if not eh_gestora(): return "sem permissão", 403
    tipo = request.form.get("tipo"); acao = request.form.get("acao")
    conn = db(); cur = DB.cur_dict(conn)
    if acao == "novo":
        rotulo = request.form.get("rotulo", "").strip()
        secao = request.form.get("secao", "").strip() or "Campos da Gestora"
        if rotulo:
            chave = slug(rotulo)
            cur.execute("SELECT 1 AS x FROM campos_config WHERE tipo=%s AND chave=%s", (tipo, chave))
            if cur.fetchone():
                chave = chave + "_2"
            cur.execute("INSERT INTO campos_config (tipo, chave, rotulo, secao, origem) VALUES (%s,%s,%s,%s,'gestora') ON CONFLICT (tipo,chave) DO NOTHING",
                        (tipo, chave, rotulo, secao))
    elif acao == "excluir":
        cur.execute("DELETE FROM campos_config WHERE id=%s AND origem='gestora'", (request.form.get("id"),))
    else:
        for r in request.form.getlist("linha"):
            ativo = 1 if request.form.get(f"ativo_{r}") else 0
            vm = request.form.get(f"vm_{r}") or None
            va = request.form.get(f"va_{r}") or None
            cur.execute("UPDATE campos_config SET ativo=%s, vigente_mes=%s, vigente_ano=%s WHERE id=%s", (ativo, vm, va, r))
    conn.commit(); conn.close()
    return redirect(url_for("gestao_campos", tipo=tipo))

# ================= USUÁRIOS =================
@app.route("/usuarios", methods=["GET", "POST"])
def usuarios():
    if not eh_gestora(): return redirect(url_for("dashboard"))
    conn = db(); cur = DB.cur_dict(conn)
    if request.method == "POST":
        acao = request.form.get("acao")
        if acao == "vincular":
            cur.execute("INSERT INTO usuario_unidades (user_id, unidade_id) VALUES (%s,%s) ON CONFLICT (user_id,unidade_id) DO NOTHING",
                        (request.form.get("user_id"), request.form.get("unidade_id")))
        elif acao == "desvincular":
            cur.execute("DELETE FROM usuario_unidades WHERE id=%s", (request.form.get("link_id"),))
        elif acao == "remover":
            uid = request.form.get("user_id")
            cur.execute("DELETE FROM usuario_unidades WHERE user_id=%s", (uid,))
            cur.execute("DELETE FROM usuarios WHERE id=%s AND papel='equipamento' AND origem='gestora'", (uid,))
        elif acao == "novo":
            email = request.form.get("email", "").strip().lower()
            if email:
                cur.execute("INSERT INTO usuarios (email, papel, origem) VALUES (%s,%s,'gestora') ON CONFLICT (email) DO NOTHING",
                            (email, request.form.get("papel", "equipamento")))
                cur.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
                uid = cur.fetchone()["id"]
                if request.form.get("unidade_id"):
                    cur.execute("INSERT INTO usuario_unidades (user_id, unidade_id) VALUES (%s,%s) ON CONFLICT (user_id,unidade_id) DO NOTHING",
                                (uid, request.form.get("unidade_id")))
        conn.commit()
    cur.execute("""SELECT u.id, u.email, u.papel, u.origem,
        (SELECT STRING_AGG(u2.nome, ' | ') FROM usuario_unidades vu
         JOIN unidades u2 ON u2.id = vu.unidade_id WHERE vu.user_id = u.id) AS unidades
        FROM usuarios u ORDER BY u.papel, u.email""")
    rows = cur.fetchall()
    cur.execute("""SELECT vu.id, u.email, u2.nome FROM usuario_unidades vu
        JOIN usuarios u ON u.id = vu.user_id JOIN unidades u2 ON u2.id = vu.unidade_id
        ORDER BY u.email, u2.nome""")
    links = cur.fetchall()
    cur.execute("SELECT id, nome FROM unidades ORDER BY nome")
    unidades = cur.fetchall()
    conn.close()
    return render_template("usuarios.html", rows=rows, links=links, unidades=unidades)

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if not session.get("user"): return redirect(url_for("login"))
    if not eh_gestora(): return redirect(url_for("painel"))
    conn = db(); cur = DB.cur_dict(conn)
    cur.execute("SELECT id, nome, tipo FROM unidades ORDER BY tipo, nome")
    unidades = cur.fetchall()
    cur.execute("SELECT id, nome_filtro, parametros FROM filtros_salvos WHERE email_usuario=%s ORDER BY id DESC", (session["user"],))
    filtros = cur.fetchall()
    conn.close()
    return render_template("dashboard.html",
                           unidades_json=json.dumps([dict(u) for u in unidades]), filtros=filtros)

@app.route("/api/campos")
def api_campos():
    return jsonify(lista_campos(request.args.get("tipo", "cras")))

def ler_filtro():
    tipo = request.args.get("tipo", "cras")
    mi, ai = int(request.args.get("mi", 1)), int(request.args.get("ai", 2026))
    mf, af = int(request.args.get("mf", 12)), int(request.args.get("af", 2026))
    chaves = [c for c in request.args.get("chaves", "").split(",") if c]
    unids = [int(u) for u in request.args.get("unidades", "").split(",") if u]
    return tipo, mi, ai, mf, af, chaves, unids

def meses_periodo(mi, ai, mf, af):
    out, a, m = [], ai, mi
    while (a, m) <= (af, mf):
        out.append((m, a)); m += 1
        if m > 12: m, a = 1, a + 1
    return out

@app.route("/api/dados")
def api_dados():
    tipo, mi, ai, mf, af, chaves, unids = ler_filtro()
    periodo = meses_periodo(mi, ai, mf, af)
    conn = db(); cur = DB.cur_dict(conn)
    if tipo == "especial":
        q = "SELECT u.nome, r.mes, r.ano, r.dados FROM relatorios r JOIN unidades u ON u.id=r.unidade_id WHERE r.tipo IN (%s)" % ",".join(["%s"]*len(TIPOS_ESPECIAIS))
        p = list(TIPOS_ESPECIAIS)
    else:
        q = "SELECT u.nome, r.mes, r.ano, r.dados FROM relatorios r JOIN unidades u ON u.id=r.unidade_id WHERE r.tipo=%s"
        p = [tipo]
    if unids:
        q += " AND u.id IN (%s)" % ",".join(["%s"]*len(unids)); p += unids
    cur.execute(q, p)
    rows = cur.fetchall()
    conn.close()
    serie = {f"{m}/{a}": {c: 0 for c in chaves} for (m, a) in periodo}
    por_unidade, por_unidade_mes, status, detalhes = {}, {}, {}, []
    for r in rows:
        dados = json.loads(r["dados"]) if r["dados"] else {}
        status.setdefault(r["nome"], set()).add(f"{r['mes']}/{r['ano']}")
        if (r["mes"], r["ano"]) not in periodo: continue
        mes_ano = f"{r['mes']}/{r['ano']}"
        por_unidade.setdefault(r["nome"], {c: 0 for c in chaves})
        por_unidade_mes.setdefault(r["nome"], {}).setdefault(mes_ano, {c: 0 for c in chaves})
        linha = {"unidade": r["nome"], "mes_ano": mes_ano}
        for c in chaves:
            v = dados.get(c); v = v if isinstance(v, (int, float)) else 0
            serie[mes_ano][c] += v
            por_unidade[r["nome"]][c] += v
            por_unidade_mes[r["nome"]][mes_ano][c] = v
            linha[c] = v
        detalhes.append(linha)
    return jsonify({"periodo": [f"{m}/{a}" for (m, a) in periodo],
                    "serie": [{**{"mes": k}, **serie[k]} for k in serie],
                    "por_unidade": [{**{"unidade": k}, **por_unidade[k]} for k in sorted(por_unidade)],
                    "por_unidade_mes": por_unidade_mes,
                    "detalhes": sorted(detalhes, key=lambda d: (d["mes_ano"], d["unidade"])),
                    "status": {u: sorted(s) for u, s in status.items()}})

@app.route("/filtros/salvar", methods=["POST"])
def salvar_filtro():
    if not eh_gestora(): return "sem permissão", 403
    conn = db(); cur = conn.cursor()
    cur.execute("INSERT INTO filtros_salvos (email_usuario, nome_filtro, tipo_relatorio, parametros) VALUES (%s,%s,%s,%s)",
                (session["user"], request.form["nome"], request.form["tipo"], request.form["parametros"]))
    conn.commit(); conn.close()
    return redirect(url_for("dashboard"))

@app.route("/exportar")
def exportar():
    if not eh_gestora(): return "sem permissão", 403
    tipo, mi, ai, mf, af, chaves, unids = ler_filtro()
    periodo = meses_periodo(mi, ai, mf, af)
    rotulos = {c["chave"]: c["rotulo"] for c in lista_campos(tipo)}
    conn = db(); cur = DB.cur_dict(conn)
    if tipo == "especial":
        q = "SELECT u.nome, r.mes, r.ano, r.dados FROM relatorios r JOIN unidades u ON u.id=r.unidade_id WHERE r.tipo IN (%s)" % ",".join(["%s"]*len(TIPOS_ESPECIAIS))
        p = list(TIPOS_ESPECIAIS)
    else:
        q = "SELECT u.nome, r.mes, r.ano, r.dados FROM relatorios r JOIN unidades u ON u.id=r.unidade_id WHERE r.tipo=%s"
        p = [tipo]
    if unids:
        q += " AND u.id IN (%s)" % ",".join(["%s"]*len(unids)); p += unids
    cur.execute(q, p)
    rows = cur.fetchall()
    conn.close()
    wb = Workbook(); ws = wb.active; ws.title = "Relatório"
    ws.append(["Unidade", "Mês/Ano"] + [rotulos.get(c, c) for c in chaves])
    for r in sorted(rows, key=lambda x: (x["ano"], x["mes"], x["nome"])):
        if (r["mes"], r["ano"]) not in periodo: continue
        dados = json.loads(r["dados"]) if r["dados"] else {}
        ws.append([r["nome"], f"{r['mes']}/{r['ano']}"] + [dados.get(c, "") for c in chaves])
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"relatorio_{tipo}_{mi}-{ai}_a_{mf}-{af}.xlsx")

# ================= BACKUP / RESTAURAR =================
@app.route("/backup")
def backup():
    if not eh_gestora(): return "sem permissão", 403
    return send_file(io.BytesIO(DB.exportar_sqlite_bytes()), as_attachment=True,
                     download_name="sistema_backup.db")

@app.route("/restaurar", methods=["POST"])
def restaurar():
    if not eh_gestora(): return "sem permissão", 403
    f = request.files.get("arquivo")
    if not f: return redirect(url_for("dashboard"))
    if not DB.importar_sqlite_bytes(f.read()):
        return "Arquivo inválido (não é um backup do sistema).", 400
    return redirect(url_for("dashboard"))

# ================= HELPERS =================
def slug(t):
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9]+", "_", t).strip("_")
    return ("campo_" + t)[:80]

def secoes_do(tipo, mes=None, ano=None):
    conn = db(); cur = DB.cur_dict(conn)
    cur.execute("SELECT chave, rotulo, secao, ativo, vigente_mes, vigente_ano FROM campos_config WHERE tipo=%s ORDER BY id", (tipo,))
    rows = cur.fetchall()
    conn.close()
    if not rows:
        secs = [(s, list(l)) for s, l in campos.CAMPOS[tipo]["secoes"]]
        ex = ajustes.CAMPOS_EXTRAS.get(tipo)
        if ex: secs.append(("Complemento", list(ex)))
        return secs
    out, ordem = {}, []
    for r in rows:
        visivel = bool(r["ativo"])
        if mes is not None and r["vigente_mes"] and r["vigente_ano"]:
            antes = (r["vigente_ano"], r["vigente_mes"]) > (ano, mes)
            visivel = visivel != antes
        if not visivel: continue
        if r["secao"] not in ordem: ordem.append(r["secao"])
        out.setdefault(r["secao"], []).append((r["chave"], r["rotulo"]))
    return [(s, out[s]) for s in ordem]

def lista_campos(tipo):
    return [{"chave": k, "rotulo": r, "secao": s} for s, l in secoes_do(tipo) for k, r in l]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)),
            debug=os.environ.get("FLASK_DEBUG", "0") == "1")