# -*- coding: utf-8 -*-
import db as DB

UNIDADES_SEED = [
    ("CRAS Cecap", "cras"), ("CRAS Central", "cras"), ("CRAS Cruzeiro do Sul", "cras"),
    ("CRAS Hortênsias", "cras"), ("CRAS Maria Luiza", "cras"), ("CRAS Parque São Paulo", "cras"),
    ("CRAS São Rafael", "cras"), ("CRAS Selmi Dei", "cras"), ("CRAS Vale do Sol", "cras"),
    ("CRAS Valle Verde", "cras"), ("CRAS Yolanda Ópice", "cras"),
    ("Casa de Acolhida", "acolhida"), ("Centro Pop", "centro_pop"),
    ("Centro Dia do Idoso", "centro_dia_idoso"), ("Residência Inclusiva", "residencia_inclusiva"),
    ("República Idosos Recanto Feliz", "republica_idosos"), ("República Idosos Vila Dignidade", "republica_idosos"),
    ("PROMAIP Feminino", "promaip"), ("PROMAIP Masculino", "promaip"), ("CREAS", "creas"),
]

USUARIOS_SEED = [
    ("gestora.assistencia@araraquara.sp.gov.br", "gestora", []),
    ("cecap@araraquara.sp.gov.br", "equipamento", ["CRAS Cecap"]),
    ("central@araraquara.sp.gov.br", "equipamento", ["CRAS Central"]),
    ("cruzeiro@araraquara.sp.gov.br", "equipamento", ["CRAS Cruzeiro do Sul"]),
    ("hortencias@araraquara.sp.gov.br", "equipamento", ["CRAS Hortênsias"]),
    ("maria.luiza@araraquara.sp.gov.br", "equipamento", ["CRAS Maria Luiza"]),
    ("pq.sao.paulo@araraquara.sp.gov.br", "equipamento", ["CRAS Parque São Paulo"]),
    ("sao.rafael@araraquara.sp.gov.br", "equipamento", ["CRAS São Rafael"]),
    ("selmi.dei@araraquara.sp.gov.br", "equipamento", ["CRAS Selmi Dei"]),
    ("vale.do.sol@araraquara.sp.gov.br", "equipamento", ["CRAS Vale do Sol"]),
    ("valle.verde@araraquara.sp.gov.br", "equipamento", ["CRAS Valle Verde"]),
    ("yolanda.opice@araraquara.sp.gov.br", "equipamento", ["CRAS Yolanda Ópice"]),
    ("creas@araraquara.sp.gov.br", "equipamento", ["CREAS"]),
    ("dia.idosos@araraquara.sp.gov.br", "equipamento", ["Centro Dia do Idoso"]),
    ("pop@araraquara.sp.gov.br", "equipamento", ["Centro Pop"]),
    ("acolhida@araraquara.sp.gov.br", "equipamento", ["Casa de Acolhida"]),
    ("promaip@araraquara.sp.gov.br", "equipamento", ["PROMAIP Feminino", "PROMAIP Masculino"]),
    ("ri@araraquara.sp.gov.br", "equipamento", ["Residência Inclusiva"]),
    ("vila.dignidade@araraquara.sp.gov.br", "equipamento", ["República Idosos Vila Dignidade"]),
    ("recanto.feliz@araraquara.sp.gov.br", "equipamento", ["República Idosos Recanto Feliz"]),
]

def init_db():
    conn = DB.get_conn(); cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS unidades (
        id SERIAL PRIMARY KEY, nome VARCHAR(100) NOT NULL, tipo VARCHAR(50) NOT NULL, UNIQUE(nome, tipo))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS relatorios (
        id SERIAL PRIMARY KEY, unidade_id INTEGER NOT NULL REFERENCES unidades(id),
        tipo VARCHAR(50) NOT NULL, mes INTEGER NOT NULL, ano INTEGER NOT NULL,
        email_usuario VARCHAR(100), data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        dados TEXT, UNIQUE(unidade_id, mes, ano))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS filtros_salvos (
        id SERIAL PRIMARY KEY, email_usuario VARCHAR(100), nome_filtro VARCHAR(100),
        tipo_relatorio VARCHAR(50), parametros TEXT, data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY, email VARCHAR(120) UNIQUE NOT NULL,
        papel VARCHAR(20) DEFAULT 'equipamento', unidade_id INTEGER,
        origem VARCHAR(20), criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS usuario_unidades (
        id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES usuarios(id),
        unidade_id INTEGER NOT NULL REFERENCES unidades(id), UNIQUE(user_id, unidade_id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS campos_config (
        id SERIAL PRIMARY KEY, tipo VARCHAR(50) NOT NULL, chave VARCHAR(100) NOT NULL,
        rotulo VARCHAR(255) NOT NULL, secao VARCHAR(100), ativo INTEGER DEFAULT 1,
        vigente_mes INTEGER, vigente_ano INTEGER, origem VARCHAR(20) DEFAULT 'dna',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(tipo, chave))""")
    conn.commit()

    cur = DB.cur_dict(conn)
    for nome, tipo in UNIDADES_SEED:
        cur.execute("INSERT INTO unidades (nome, tipo) VALUES (%s,%s) ON CONFLICT (nome,tipo) DO NOTHING", (nome, tipo))
    for email, papel, unids in USUARIOS_SEED:
        cur.execute("INSERT INTO usuarios (email, papel, origem) VALUES (%s,%s,'seed') ON CONFLICT (email) DO NOTHING", (email, papel))
        cur.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
        uid = cur.fetchone()["id"]
        for nome in unids:
            cur.execute("SELECT id FROM unidades WHERE nome=%s", (nome,))
            r = cur.fetchone()
            if r:
                cur.execute("INSERT INTO usuario_unidades (user_id, unidade_id) VALUES (%s,%s) ON CONFLICT (user_id,unidade_id) DO NOTHING", (uid, r["id"]))
    for email, papel, _ in USUARIOS_SEED:
        cur.execute("UPDATE usuarios SET papel=%s, origem=COALESCE(origem,'seed') WHERE email=%s", (papel, email))
    conn.commit()

    cur.execute("SELECT COUNT(*) AS n FROM campos_config")
    n = cur.fetchone()["n"]
    if n == 0:
        import campos, ajustes
        for tipo, defn in campos.CAMPOS.items():
            secs = [(s, list(l)) for s, l in defn["secoes"]]
            ex = ajustes.CAMPOS_EXTRAS.get(tipo)
            if ex: secs.append(("Complemento", list(ex)))
            for sec, lista in secs:
                for chave, rotulo in lista:
                    cur.execute("INSERT INTO campos_config (tipo, chave, rotulo, secao) VALUES (%s,%s,%s,%s) ON CONFLICT (tipo,chave) DO NOTHING",
                                (tipo, chave, rotulo, sec))
        conn.commit()
    conn.close()
    print("✅ Banco Postgres pronto.")

if __name__ == '__main__':
    init_db()