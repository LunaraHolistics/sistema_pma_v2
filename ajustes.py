# -*- coding: utf-8 -*-
# Dicionários de calibração da importação (não mexe no DNA principal)

ANO_PADRAO = 2026   # usado quando o arquivo tem o mês no nome mas nenhum ano

# Correções manuais de mês/ano por trecho do nome do arquivo
AJUSTES_MANUAIS = {
    "3 marco aline":                 (3, 2026),
    "copia de 01 janeiro asenilda":  (1, 2026),
    "3_relatorio_mensal_marco":      (3, 2026),
    "4_relatorio_mensal_abril":      (4, 2026),
    "relatorio_mensal_fevereiro":    (2, 2026),
    "relatorio_mensal_janeiro":      (1, 2026),
    "abril (5)":                     (4, 2026),
    "maio(1)":                       (5, 2026),
    "selmi_dei_julho":               (7, 2026),
}

# Rótulos que devem ser ignorados silenciosamente (texto livre / cabeçalhos)
IGNORE_PREFIX = [
    "tema da s", "servico nao executado", "funcao no cras", "nome do funcionario",
    "equipe do cras", "matricula", "data", "nome do coordenador", "nome do chefe",
    "observacao", "endereco", "capacidade de atendimento 20",
]

# Rótulo normalizado -> chave do banco (casos exatos)
ALIASES = {
    "n de familias com criancas e adolescentes em trab infantil": "perfil_trabalho_infantil",
    "n de familias com criancas e adolescentes em acolhimento": "perfil_acolhimento_criancas",
    "n de encaminhamento para insercao em programas e servicos": "enc_programas_socioassistenciais",
}

# Início do rótulo normalizado -> chave (casos truncados/complementados)
ALIASES_PREFIX = [
    ("n de oficinas realizadas em parceria com esporte", "oficinas_esporte"),
    ("n de oficinas realizadas em parceria com a cultura", "oficinas_cultura"),
    ("total de projetos acoes coletivas realizados no territorio", "territorio_projetos"),
    ("n de encaminhamentos para a sistema de defesa de direitos", "enc_defesa_direitos"),
    ("pcd nao inserido em", "perfil_pcd"),
]

# Campos que existem nas planilhas mensais mas ainda não estavam no DNA
CAMPOS_EXTRAS = {
    "centro_dia_idoso": [
        ("total_idosos_atendimento", "Nº total de pessoas idosas em atendimento"),
        ("idosos_desligados_mes", "Nº de pessoas idosas desligadas, durante o mês de referência"),
        ("idosos_inseridos_mes", "Nº de pessoas idosas inseridas, durante o mês de referência"),
        ("idosos_afastados_saude", "Nº de pessoas idosas afastadas, durante o mês para tratamento de saúde"),
        ("idosos_lista_espera", "Nº de pessoas idosas em lista de espera"),
        ("solicitacoes_vaga_mes", "Nº solicitações de vagas no mês"),
        ("vagas_fora_criterios", "Nº vagas solicitadas no mês fora dos critérios do Serviço"),
        ("atd_grupo_familias", "Nº de atendimentos em grupo com as famílias"),
    ],
    "republica_idosos": [
        ("relatorios_tecnicos_grupais", "Nº de relatórios técnicos elaborado"),
    ],
    "acolhida": [
        ("capacidade_atendimento", "Capacidade de atendimento"),
        ("total_pessoas_atendidas", "Total de Pessoas atendidas no mês"),
        ("total_usuarios_cadunico", "Total de usuários inscritos no Cadastro Único"),
        ("enc_seas", "Encaminhamentos pelo SEAS"),
        ("acesso_demanda_espontanea", "Demanda Espontânea"),
        ("acesso_telefone", "Solicitação de atendimento através de contato telefônico"),
        ("acesso_demais_politicas", "Demais Políticas Públicas e órgãos da administração pública"),
        ("acesso_servico_pop_rua", "Serviço público de atend/o à pop de rua"),
        ("acesso_prot_basica", "Proteção Social Básica"),
        ("acesso_prot_especial", "Proteção Social Especial"),
        ("acesso_consultorio_rua", "Consultório na Rua"),
        ("usuarios_acomp_sistematico", "Nº de usuários em acompanhamento sistemático pelo serviço"),
        ("usuarios_inseridos_acomp", "Nº de usuários inseridos em acompanhamento sistemático"),
        ("usuarios_desligados_acomp", "Nº de usuários desligados do acompanhamento sistemático"),
        ("usuarios_pbf", "Nº de usuários beneficiários do PBF"),
        ("usuarios_prog_municipais", "Nº de usuários beneficiários de Prog. Municipais"),
        ("atividades_externas", "Nº de atividades externas com usuários"),
        ("atendimentos_familia", "Nº de Atendimentos à família dos usuários do serviço"),
        ("animais_acolhidos", "Nº de animais acolhidos"),
        ("inclusoes_cadunico", "Nº de usuários incluídos no Cadastro Único"),
        ("atualizacoes_cadunico", "Nº de atualizações do Cadastro Único para Programas Sociais"),
        ("usuarios_bpc", "Nº de usuários beneficiários do BPC"),
        ("enc_saude", "Unidades da Sec. Munic. De Saúde"),
        ("enc_outras_politicas", "Outras Políticas Públicas e serviços locais"),
        ("enc_prot_basica", "Proteção Social Básica"),
        ("enc_prot_especial", "Proteção Social Especial"),
        ("enc_rede_privada", "Rede Socioassistencial Privada"),
        ("enc_orgao_defesa", "Órgão de Defesa de Direito"),
        ("enc_obtencao_doc", "Obtenção de documentos"),
        ("enc_solicitacao_bpc", "Solicitação de BPC"),
        ("superaram_rua", "Pessoas que conseguiram superar a situação de rua"),
        ("lgbtqia", "Nº de usuários que se declaram LGBTQIA+"),
        ("vinculos_rompidos", "Nº de usuários com familiares na cidade, mas com vínculos rompidos"),
        ("vinculos_fragilizados", "Nº de usuários com familiares na cidade, mas com vínculos bastante fragilizados"),
        ("sem_vinculos", "Nº de usuários sem vínculos familiares na cidade"),
        ("renda_ausencia", "Nº de usuários com ausência de remuneração"),
        ("renda_ate_meio_sm", "Nº de usuários com renda per capita familiar mensal de até ½ sal.min"),
        ("renda_ate_3_sm", "Nº de usuários com renda per capita familiar mensal de até 3 sal.min"),
        ("carac_bebida", "Pessoas que fazem uso abusivo apenas de bebida alcoolica"),
        ("carac_drogas_bebida", "Pessoas adultas usuárias de drogas ilícitas e bebida alcoolica"),
        ("carac_doenca_def_transtorno", "Pessoas com doença, deficiência ou transtorno mental"),
        ("carac_def_fisica", "Pessoas com deficiência física"),
    ],
    "centro_pop": [
        ("capacidade_atendimento", "Capacidade de atendimento"),
        ("total_pessoas_atendidas", "Total de Pessoas atendidas no mês"),
        ("total_usuarios_cadunico", "Total de usuários inscritos no Cadastro Único"),
        ("enc_seas", "Encaminhamentos pelo SEAS"),
        ("acesso_demanda_espontanea", "Demanda Espontânea"),
        ("acesso_telefone", "Solicitação de atendimento através de contato telefônico"),
        ("acesso_demais_politicas", "Demais Políticas Públicas e órgãos da administração pública"),
        ("acesso_consultorio_rua", "Consultório na Rua"),
        ("usuarios_acomp_sistematico", "Nº de usuários em acompanhamento sistemático pelo serviço"),
        ("usuarios_inseridos_acomp", "Nº de usuários inseridos em acompanhamento sistemático"),
        ("usuarios_desligados_acomp", "Nº de usuários desligados do acompanhamento sistemático"),
        ("usuarios_pbf", "Nº de usuários beneficiários do PBF"),
        ("usuarios_prog_municipais", "Nº de usuários beneficiários de Prog. Municipais"),
        ("atividades_externas", "Nº de atividades externas com usuários"),
        ("atendimentos_familia", "Nº de Atendimentos à família dos usuários do serviço"),
        ("inclusoes_cadunico", "Nº de usuários incluídos no Cadastro Único"),
        ("atualizacoes_cadunico", "Nº de atualizações do Cadastro Único para Programas Sociais"),
        ("usuarios_bpc", "Nº de usuários beneficiários do BPC"),
        ("enc_saude", "Unidades da Sec. Munic. De Saúde"),
        ("enc_outras_politicas", "Outras Políticas Públicas e serviços locais"),
        ("superaram_rua", "Pessoas que conseguiram superar a situação de rua"),
        ("lgbtqia", "Nº de usuários que se declaram LGBTQIA+"),
        ("vinculos_rompidos", "Nº de usuários com familiares na cidade, mas com vínculos rompidos"),
        ("vinculos_fragilizados", "Nº de usuários com familiares na cidade, mas com vínculos bastante fragilizados"),
        ("sem_vinculos", "Nº de usuários sem vínculos familiares na cidade"),
        ("itinerante_cadunico", "Itinerante que possui Cadastro Único"),
        ("renda_ausencia", "Com ausência de remuneração"),
        ("renda_ate_meio_sm", "Até ½ sal.min"),
        ("renda_ate_3_sm", "Até 3 sal.min"),
        ("carac_bebida", "Pessoas que fazem uso abusivo apenas de bebida alcoolica"),
        ("carac_drogas_bebida", "Pessoas adultas usuárias de drogas ilícitas e bebida alcoolica"),
        ("carac_doenca_def_transtorno", "Pessoas com doença, deficiência ou transtorno mental"),
        ("carac_def_fisica", "Pessoas com deficiência física"),
        ("enc_terminal_rodoviario", "Nº de pessoas encaminhadas para o terminal rodoviário"),
        ("enc_residencia", "Nº de pessoas encaminhadas para sua residência"),
        ("enc_cadunico_realizacao", "Nº de pessoas encaminhadas para realização de Cadastro Único"),
        ("chamados_solicitacoes", "Nº de chamados/solicitações"),
        ("deslocamentos_busca_ativa", "Nº de deslocamento para atendimento de busca ativa"),
    ],
}