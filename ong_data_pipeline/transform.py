import logging
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)


def _strip_texto(df: pd.DataFrame, colunas: list) -> pd.DataFrame:
    for col in colunas:
        df[col] = df[col].astype(str).str.strip().str.title()
    return df


def _opcional_para_string(df: pd.DataFrame, colunas: list) -> pd.DataFrame:
    for col in colunas:
        df[col] = df[col].fillna("").astype(str).str.strip().str.title()
    return df


def _id_para_string(df: pd.DataFrame, colunas: list) -> pd.DataFrame:
    for col in colunas:
        df[col] = df[col].apply(
            lambda x: str(int(x)) if pd.notna(x) and str(x).strip() != "" else ""
        )
    return df



# ---------------------------------------------------------------------------
#   Constantes — Formulário 1
# ---------------------------------------------------------------------------

# Multi-choice: valores exatos que o Forms entrega
CONDICAO_VALIDA = {"Saudável", "Ferido", "Doente", "Desnutrido", "Desconhecido"}


def _normalizar_condicao(valor: str) -> str:
    """
    Condição de Saúde é multi-choice — pode chegar como "Ferido, Doente".
    Valida cada parte individualmente contra os valores do Forms.
    Usa comparação case-insensitive para proteger contra variações de entrega do Sheets.
    """
    mapa = {v.lower(): v for v in CONDICAO_VALIDA}
    partes    = [p.strip() for p in valor.split(",")]
    validas   = [mapa[p.lower()] for p in partes if p.lower() in mapa]
    invalidas = [p for p in partes if p.lower() not in mapa]

    if invalidas:
        log.warning(f"[SILVER] Condição de saúde não reconhecida: {invalidas} → ignorada")

    return ", ".join(validas) if validas else "Desconhecido"


# ---------------------------------------------------------------------------
#   Formulário 1 — Entrada / Novo Resgate
# ---------------------------------------------------------------------------

def transformar_entradas(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Bronze → Silver: Entrada / Novo Resgate

    O Forms garante: valores de dropdown válidos, regex em campos de texto,
    data em formato consistente, todos os campos [REQ] preenchidos.

    Responsabilidade do pandas: strip de espaços, tipagem de datas,
    split do campo multi-choice, sanitização do texto livre.
    """
    log.info("[SILVER] Iniciando transformação: Entrada / Novo Resgate")

    df = df_raw.copy()

    # 1. Limpar espaços dos nomes de colunas — artefato do Sheets
    df.columns = df.columns.str.strip()

    # 2. Selecionar e renomear
    df = df[[
        "Carimbo de data/hora",
        "Endereço de e-mail",
        "Data de Entrada",
        "Nome do Responsável",
        "Sobrenome do Responsável",
        "Espécie do animal",
        "Sexo",
        "Porte",
        "Condição de Saúde",
        "Histórico/Observações do Resgate",
    ]].copy()

    df = df.rename(columns={
        "Carimbo de data/hora":             "carimbo_ts",
        "Endereço de e-mail":               "email_responsavel",
        "Data de Entrada":                  "data_entrada",
        "Nome do Responsável":              "nome_responsavel",
        "Sobrenome do Responsável":         "sobrenome_responsavel",
        "Espécie do animal":                "especie",
        "Sexo":                             "sexo",
        "Porte":                            "porte",
        "Condição de Saúde":                "condicao_saude",
        "Histórico/Observações do Resgate": "historico",
    })

    # 3. Carimbo — datetime do Sheets, remover microssegundos
    df["carimbo_ts"] = pd.to_datetime(df["carimbo_ts"], errors="coerce").dt.floor("s")

    # 4. Data de Entrada — [REQ], manter só a data sem hora
    df["data_entrada"] = pd.to_datetime(df["data_entrada"], errors="coerce").dt.date

    nulos = df["data_entrada"].isna().sum()
    if nulos > 0:
        log.warning(f"[SILVER] {nulos} data(s) de entrada inválida(s) → revisar na origem")

    # 5. E-mail — lowercase + strip
    df["email_responsavel"] = (
        df["email_responsavel"].astype(str).str.strip().str.lower()
    )

    # 6. Nome e sobrenome — Forms valida regex mas não remove trailing spaces
    df["nome_responsavel"]      = df["nome_responsavel"].astype(str).str.strip().str.title()
    df["sobrenome_responsavel"] = df["sobrenome_responsavel"].astype(str).str.strip().str.title()
    df["nome_completo"]         = (df["nome_responsavel"] + " " + df["sobrenome_responsavel"]).str.strip()

    # 7. Dropdowns — Forms garante valor válido, só strip
    df["especie"] = df["especie"].astype(str).str.strip()
    df["sexo"]    = df["sexo"].astype(str).str.strip()
    df["porte"]   = df["porte"].astype(str).str.strip()

    # 8. Condição de Saúde — multi-choice, validar cada valor individualmente
    df["condicao_saude"]         = df["condicao_saude"].astype(str).str.strip().apply(_normalizar_condicao)
    df["flag_multiplas_condicoes"] = df["condicao_saude"].str.contains(",").astype(int)

    # 9. Histórico — único campo não obrigatório
    #    fillna("") antes do astype(str) evita que NaN vire a string "nan"
    df["historico"] = (
        df["historico"]
        .fillna("")
        .astype(str)
        .str.replace(r"\\n", " ", regex=True)   # \n literal vindo do Forms
        .str.replace(r"\n",  " ", regex=True)    # quebra de linha real
        .str.replace(r"\s+", " ", regex=True)    # múltiplos espaços
        .str.strip()
    )

    log.info(f"[SILVER] Entradas: {len(df)} registros transformados")
    return df

# ---------------------------------------------------------------------------
#   Formulário 2 — Controle de Doações
# ---------------------------------------------------------------------------

TIPOS_DOACAO_VALIDOS = {"Dinheiro", "Ração", "Medicamentos", "Acessórios/Roupinhas"}
TIPOS_DOADOR_VALIDOS = {"Anônimo", "Identificado"}


def _validar_condicionais_doacoes(df: pd.DataFrame) -> None:
    """
    Valida a consistência dos campos condicionais sem bloquear o pipeline.
    Loga anomalias para revisão na origem.
    """
    # Medicamentos: categoria e nome são [REQ] quando tipo == "Medicamentos"
    mask_med = df["tipo_doacao"] == "Medicamentos"
    nulos_categoria = df.loc[mask_med, "categoria_medicamento"].replace("", pd.NA).isna().sum()
    nulos_nome_med  = df.loc[mask_med, "nome_medicamento"].replace("", pd.NA).isna().sum()

    if nulos_categoria > 0:
        log.warning(f"[SILVER] {nulos_categoria} doação(ões) de Medicamentos sem categoria → revisar na origem")
    if nulos_nome_med > 0:
        log.warning(f"[SILVER] {nulos_nome_med} doação(ões) de Medicamentos sem nome específico → revisar na origem")

    # Dinheiro: valor_doado é [REQ] quando tipo == "Dinheiro"
    mask_din = df["tipo_doacao"] == "Dinheiro"
    nulos_valor = df.loc[mask_din, "valor_doado"].isna().sum()
    if nulos_valor > 0:
        log.warning(f"[SILVER] {nulos_valor} doação(ões) em Dinheiro sem valor informado → revisar na origem")

    # Identificado: nome_doador é [REQ] quando tipo_doador == "Identificado"
    mask_id = df["tipo_doador"] == "Identificado"
    nulos_nome = df.loc[mask_id, "nome_doador"].replace("", pd.NA).isna().sum()
    if nulos_nome > 0:
        log.warning(f"[SILVER] {nulos_nome} doador(es) Identificado(s) sem nome → revisar na origem")


def transformar_doacoes(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Bronze → Silver: Controle de Doações

    Campos condicionais por ramificação do Forms:
      tipo_doacao == "Medicamentos" → categoria_medicamento, nome_medicamento [REQ]
      tipo_doacao == "Dinheiro"     → valor_doado [REQ]
      tipo_doacao outro             → campos acima chegam NaN (esperado)
      tipo_doador == "Identificado" → nome_doador [REQ]
      tipo_doador == "Anônimo"      → nome_doador NaN (esperado, não erro)
    """
    log.info("[SILVER] Iniciando transformação: Controle de Doações")

    df = df_raw.copy()

    # 1. Limpar espaços dos nomes de colunas
    df.columns = df.columns.str.strip()

    # 2. Selecionar e renomear
    df = df[[
        "Carimbo de data/hora",
        "Endereço de e-mail",
        "Data da Doação",
        "Tipo de Doação",
        "Categoria do Medicamento",
        "Nome específico",
        "Valor Doado (R$)",
        "Tipo de Doador",
        "Nome do Doador",
    ]].copy()

    df = df.rename(columns={
        "Carimbo de data/hora":   "carimbo_ts",
        "Endereço de e-mail":     "email_doador",
        "Data da Doação":         "data_doacao",
        "Tipo de Doação":         "tipo_doacao",
        "Categoria do Medicamento": "categoria_medicamento",
        "Nome específico":        "nome_medicamento",
        "Valor Doado (R$)":       "valor_doado",
        "Tipo de Doador":         "tipo_doador",
        "Nome do Doador":         "nome_doador",
    })

    # 3. Carimbo
    df["carimbo_ts"] = pd.to_datetime(df["carimbo_ts"], errors="coerce").dt.floor("s")

    # 4. Data da Doação — [REQ]
    df["data_doacao"] = pd.to_datetime(df["data_doacao"], errors="coerce").dt.date

    nulos_data = df["data_doacao"].isna().sum()
    if nulos_data > 0:
        log.warning(f"[SILVER] {nulos_data} data(s) de doação inválida(s) → revisar na origem")

    # 5. E-mail
    df["email_doador"] = df["email_doador"].astype(str).str.strip().str.lower()

    # 6. Dropdowns obrigatórios — Forms garante valor válido, só strip
    df["tipo_doacao"] = df["tipo_doacao"].astype(str).str.strip()
    df["tipo_doador"] = df["tipo_doador"].astype(str).str.strip()

    # 7. Valor Doado — condicional: só existe quando tipo_doacao == "Dinheiro"
    #    NaN para outros tipos é ESPERADO — não preencher com 0.0
    #    Converter para float garante tipagem correta para o MySQL
    df["valor_doado"] = pd.to_numeric(df["valor_doado"], errors="coerce").astype("Float64")

    # 8. Campos condicionais de Medicamentos
    #    NaN quando tipo != "Medicamentos" é ESPERADO — converter para string vazia
    #    mas apenas após a validação de consistência
    df["categoria_medicamento"] = (
        df["categoria_medicamento"].fillna("").astype(str).str.strip()
    )
    # Forms valida regex mas não remove trailing spaces
    df["nome_medicamento"] = (
        df["nome_medicamento"].fillna("").astype(str).str.strip().str.title()
    )

    # 9. Nome do Doador — condicional: NaN quando tipo_doador == "Anônimo" é ESPERADO
    df["nome_doador"] = (
        df["nome_doador"].fillna("").astype(str).str.strip().str.title()
    )

    # 10. Validar consistência dos condicionais — loga anomalias sem bloquear
    _validar_condicionais_doacoes(df)

    log.info(f"[SILVER] Doações: {len(df)} registros transformados")
    return df

# ---------------------------------------------------------------------------
#   Formulário 3 — Prontuário Médico e Rotina
# ---------------------------------------------------------------------------

# Mapa de quais campos condicionais são [REQ] por tipo de evento
# Tipos sem campos condicionais (Consulta Veterinária, Castração)
# não aparecem aqui — NaN neles é sempre esperado
CAMPOS_OBRIGATORIOS_POR_EVENTO = {
    "Medicamento": ["categoria_medicamento", "nome_medicamento"],
    "Vacina":      ["categoria_vacina", "nome_vacina"],
    "Cirurgia":    ["nome_cirurgia"],
}


def _validar_condicionais_prontuario(df: pd.DataFrame) -> None:
    """
    Valida a consistência dos campos condicionais por tipo de evento.
    NaN é esperado quando o campo não pertence ao evento da linha.
    NaN é anomalia quando o campo é [REQ] para o evento da linha.
    """
    for tipo_evento, campos in CAMPOS_OBRIGATORIOS_POR_EVENTO.items():
        mask = df["tipo_evento"] == tipo_evento
        if not mask.any():
            continue
        for campo in campos:
            # replace("", pd.NA) detecta tanto NaN quanto string vazia
            nulos = df.loc[mask, campo].replace("", pd.NA).isna().sum()
            if nulos > 0:
                log.warning(
                    f"[SILVER] {nulos} registro(s) com tipo_evento='{tipo_evento}' "
                    f"sem '{campo}' → campo [REQ] para esse evento, revisar na origem"
                )


def transformar_prontuarios(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Bronze → Silver: Prontuário Médico e Rotina

    Ramificações do Forms por Tipo do Evento:
      "Medicamento"          → categoria_medicamento [REQ], nome_medicamento [REQ]
      "Vacina"               → categoria_vacina [REQ], nome_vacina [REQ]
      "Cirurgia"             → nome_cirurgia [REQ]
      "Consulta Veterinária" → sem campos condicionais, todos NaN (esperado)
      "Castração"            → sem campos condicionais, todos NaN (esperado)

    Forms garante: tipo_evento dentro da lista, regex nos campos de texto,
    todos os [REQ] não condicionais preenchidos.
    pandas trata: strip de espaços, tipagem de datas, NaN condicionais.
    """
    log.info("[SILVER] Iniciando transformação: Prontuário Médico e Rotina")

    df = df_raw.copy()

    # 1. Limpar espaços dos nomes de colunas
    df.columns = df.columns.str.strip()

    # 2. Selecionar e renomear
    df = df[[
        "Carimbo de data/hora",
        "Endereço de e-mail",
        "Data do Procedimento",
        "Nome Do Profissional",
        "Tipo de Evento",
        "Categoria do Medicamento",
        "Nome específico Medicamento",
        "Categoria da Vacina",
        "Nome específico",
        "Nome da Cirurgia realizada",
    ]].copy()

    df = df.rename(columns={
        "Carimbo de data/hora":        "carimbo_ts",
        "Endereço de e-mail":          "email_profissional",
        "Data do Procedimento":        "data_procedimento",
        "Nome Do Profissional":        "nome_profissional",
        "Tipo de Evento":              "tipo_evento",
        "Categoria do Medicamento":    "categoria_medicamento",
        "Nome específico Medicamento": "nome_medicamento",
        "Categoria da Vacina":         "categoria_vacina",
        "Nome específico":             "nome_vacina",
        "Nome da Cirurgia realizada":  "nome_cirurgia",
    })

    # 3. Carimbo
    df["carimbo_ts"] = pd.to_datetime(df["carimbo_ts"], errors="coerce").dt.floor("s")

    # 4. Data do Procedimento — [REQ]
    df["data_procedimento"] = pd.to_datetime(
        df["data_procedimento"], dayfirst=True, errors="coerce"
    ).dt.date

    nulos_data = df["data_procedimento"].isna().sum()
    if nulos_data > 0:
        log.warning(f"[SILVER] {nulos_data} data(s) de procedimento inválida(s) → revisar na origem")

    # 5. E-mail
    df["email_profissional"] = df["email_profissional"].astype(str).str.strip().str.lower()

    # 6. Nome do profissional — [REQ], Forms valida regex, pandas remove trailing spaces
    df["nome_profissional"] = df["nome_profissional"].astype(str).str.strip().str.title()

    # 7. Tipo do Evento — [REQ] single-choice, Forms garante valor válido, só strip
    df["tipo_evento"] = df["tipo_evento"].astype(str).str.strip()

    # 8. Campos condicionais — NaN esperado quando o evento não os ativa
    #    Todos viram string vazia para consistência no banco
    #    A validação de [REQ] por evento acontece logo depois
    campos_condicionais = [
        "categoria_medicamento",
        "nome_medicamento",
        "categoria_vacina",
        "nome_vacina",
        "nome_cirurgia",
    ]
    for campo in campos_condicionais:
        df[campo] = df[campo].fillna("").astype(str).str.strip().str.title()

    # 9. Validar consistência dos condicionais por tipo de evento
    _validar_condicionais_prontuario(df)

    log.info(f"[SILVER] Prontuários: {len(df)} registros transformados")
    return df

# ---------------------------------------------------------------------------
#   Formulário 4 — Registro de Adoção / Saída
# ---------------------------------------------------------------------------

# Motivos que ativam os campos condicionais de destino
MOTIVOS_COM_DESTINO = {"Adoção Definitiva", "Lar Temporário", "Transferência"}

# Campos condicionais — todos controlados pelo mesmo motivo_saida
CAMPOS_DESTINO = [
    "nome_adotante",
    "telefone",
    "cidade_destino",
    "bairro_destino",
    "num_imovel",
    "tipo_imovel",
]


def _validar_condicionais_saidas(df: pd.DataFrame) -> None:
    """
    Valida a consistência dos campos de destino por motivo de saída.

    Motivos COM destino (Adoção Definitiva, Lar Temporário, Transferência):
      todos os campos de destino são [REQ] → NaN ou "" é anomalia
    Motivos SEM destino (Óbito, Fuga):
      todos os campos de destino chegam NaN → comportamento esperado, não loga
    """
    mask_com_destino = df["motivo_saida"].isin(MOTIVOS_COM_DESTINO)

    for campo in CAMPOS_DESTINO:
        nulos = df.loc[mask_com_destino, campo].replace("", pd.NA).isna().sum()
        if nulos > 0:
            log.warning(
                f"[SILVER] {nulos} registro(s) com motivo que exige destino "
                f"sem '{campo}' preenchido → campo [REQ] para esse motivo, "
                f"revisar na origem"
            )


def transformar_saidas(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Bronze → Silver: Registro de Adoção / Saída

    Ramificações do Forms por Motivo da Saída:
      "Adoção Definitiva"  → 6 campos de destino [REQ]
      "Lar Temporário"     → 6 campos de destino [REQ]
      "Transferência"      → 6 campos de destino [REQ]
      "Óbito"              → 6 campos de destino NaN (esperado, não loga)
      "Fuga"               → 6 campos de destino NaN (esperado, não loga)

    Forms garante: motivo dentro da lista, regex nos campos de texto,
    apenas números em telefone e nº imóvel.
    pandas trata: strip, tipagem de datas, int64 → string, NaN condicionais.
    """
    log.info("[SILVER] Iniciando transformação: Registro de Adoção / Saída")

    df = df_raw.copy()

    # 1. Limpar espaços dos nomes de colunas
    df.columns = df.columns.str.strip()

    # 2. Selecionar e renomear
    df = df[[
        "Carimbo de data/hora",
        "Data da Saída",
        "Nome do Animal",
        "Motivo da Saída",
        "Nome do Adotante/Tutor",
        "Telefone do Adotante/Tutor",
        "Cidade de Destino",
        "Bairro de Destino",
        "Nº do Imovél",
        "Tipo do Imovél",
    ]].copy()

    df = df.rename(columns={
        "Carimbo de data/hora":       "carimbo_ts",
        "Data da Saída":              "data_saida",
        "Nome do Animal":             "nome_animal",
        "Motivo da Saída":            "motivo_saida",
        "Nome do Adotante/Tutor":     "nome_adotante",
        "Telefone do Adotante/Tutor": "telefone",
        "Cidade de Destino":          "cidade_destino",
        "Bairro de Destino":          "bairro_destino",
        "Nº do Imovél":               "num_imovel",
        "Tipo do Imovél":             "tipo_imovel",
    })

    # 3. Carimbo
    df["carimbo_ts"] = pd.to_datetime(df["carimbo_ts"], errors="coerce").dt.floor("s")

    # 4. Data da Saída — [REQ]
    df["data_saida"] = pd.to_datetime(df["data_saida"], errors="coerce").dt.date

    nulos_data = df["data_saida"].isna().sum()
    if nulos_data > 0:
        log.warning(
            f"[SILVER] {nulos_data} data(s) de saída inválida(s) → revisar na origem"
        )

    # 5. Nome do Animal — [REQ], Forms valida regex, pandas remove trailing spaces
    df["nome_animal"] = df["nome_animal"].astype(str).str.strip().str.title()

    # 6. Motivo da Saída — [REQ] single-choice, Forms garante valor, só strip
    df["motivo_saida"] = df["motivo_saida"].astype(str).str.strip()

    # 7. Campos condicionais de destino
    #    fillna("") ANTES do astype(str) evita que NaN vire a string "nan"
    #    Óbito e Fuga chegam com esses campos NaN — viram "" corretamente

    # Texto livre — strip + title case
    for campo in ["nome_adotante", "cidade_destino", "bairro_destino"]:
        df[campo] = df[campo].fillna("").astype(str).str.strip().str.title()

    # Single-choice — só strip (Forms garante valor quando ativo)
    df["tipo_imovel"] = df["tipo_imovel"].fillna("").astype(str).str.strip()

    # Number → string: identificadores não são métricas
    # str(int(x)) evita o ".0" que astype(str) adiciona em floats
    df["telefone"] = df["telefone"].apply(
        lambda x: str(int(x)) if pd.notna(x) and str(x).strip() != "" else ""
    )
    df["num_imovel"] = df["num_imovel"].apply(
        lambda x: str(int(x)) if pd.notna(x) and str(x).strip() != "" else ""
    )

    # 8. Validar consistência — roda APÓS conversões para detectar "" de NaN
    #    vs. "" de campo realmente vazio em motivo que exige destino
    _validar_condicionais_saidas(df)

    log.info(f"[SILVER] Saídas: {len(df)} registros transformados")
    return df