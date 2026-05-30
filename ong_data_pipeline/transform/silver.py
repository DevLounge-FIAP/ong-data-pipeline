import logging
import pandas as pd
import hashlib

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
#   Constantes — Formulário Entrada / Novo Resgate
# ---------------------------------------------------------------------------

CONDICAO_VALIDA = {"Saudável", "Ferido", "Doente", "Desnutrido", "Desconhecido"}

def _normalizar_condicao(valor: str, erros: list[str]) -> str:
    mapa = {v.lower(): v for v in CONDICAO_VALIDA}
    partes    = [p.strip() for p in valor.split(",")]
    validas   = [mapa[p.lower()] for p in partes if p.lower() in mapa]
    invalidas = [p for p in partes if p.lower() not in mapa]

    if invalidas:
        erros.append(f"Condição de saúde não reconhecida: {', '.join(invalidas)} → ignorada")

    return ", ".join(validas) if validas else "Desconhecido"


# ---------------------------------------------------------------------------
#   Função de hash reutilizável para criar chaves únicas
# ---------------------------------------------------------------------------

def _gerar_hash(prefixo: str, texto_base: any) -> str:
    """Gera um identificador único no formato PREFIXO-XXXXXX."""
    # Garantir que o texto_base seja string mesmo que venha como pd.NA, float, etc.
    texto_str = str(texto_base) if pd.notna(texto_base) else ""
    return f"{prefixo}-" + hashlib.md5(texto_str.encode()).hexdigest()[:6].upper()


# ---------------------------------------------------------------------------
#   Formulário 1 — Entrada / Novo Resgate
# ---------------------------------------------------------------------------

def transformar_entradas(df_raw: pd.DataFrame) -> pd.DataFrame:
    log.info("[SILVER] Iniciando transformação: Entrada / Novo Resgate")
    df = df_raw.copy()
    erros_da_aba = []

    df.columns = df.columns.str.strip()

    # Ponto 2 - Proteção contra colunas amputadas
    COLUNAS_ESPERADAS = [
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
    ]
    df = df.reindex(columns=COLUNAS_ESPERADAS)

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

    # UTC explícito
    df["carimbo_ts"] = (
        pd.to_datetime(df["carimbo_ts"], dayfirst=True, errors="coerce")
        .dt.floor("s")
        .dt.tz_localize("UTC")
    )

    df["data_entrada"] = pd.to_datetime(
        df["data_entrada"], dayfirst=True, errors="coerce"
    ).dt.normalize()

    nulos_data = df["data_entrada"].isna().sum()
    if nulos_data > 0:
        erros_da_aba.append(f"{nulos_data} data(s) de entrada inválida(s) ou em branco")

    df["email_responsavel"] = df["email_responsavel"].astype(str).str.strip().str.lower()
    df["nome_responsavel"]      = df["nome_responsavel"].astype(str).str.strip().str.title()
    df["sobrenome_responsavel"] = df["sobrenome_responsavel"].astype(str).str.strip().str.title()
    df["nome_completo"]         = (df["nome_responsavel"] + " " + df["sobrenome_responsavel"]).str.strip()

    df["especie"] = df["especie"].astype(str).str.strip()
    df["sexo"]    = df["sexo"].astype(str).str.strip()
    df["porte"]   = df["porte"].astype(str).str.strip()

    df["condicao_saude"] = df["condicao_saude"].astype(str).str.strip().apply(_normalizar_condicao, args=(erros_da_aba,))
    
    df["flag_multiplas_condicoes"] = df["condicao_saude"].str.contains(",").astype(str)
    for condicao in CONDICAO_VALIDA:
        sufixo = condicao.lower().replace(' ', '_').replace('á', 'a')
        col_name = f"is_{sufixo}"
        df[col_name] = df["condicao_saude"].str.contains(condicao, case=False, na=False)
        
    if "flag_multiplas_condicoes" in df.columns:
        df["flag_multiplas_condicoes"] = df["flag_multiplas_condicoes"].replace({
            "True": 1, "False": 0,
            "true": 1, "false": 0,
            True: 1, False: 0
        }).astype("Int64")
        
    colunas_is = [col for col in df.columns if col.startswith("is_")]
    df[colunas_is] = df[colunas_is].astype("boolean")

    df["historico"] = (
        df["historico"]
        .fillna("")
        .astype(str)
        .str.replace(r"\\n", " ", regex=True)
        .str.replace(r"\n",  " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    # Ponto 3 - ID Animal (chave única)
    string_temp = (
        df["carimbo_ts"].astype(str) + "_"
        + df["nome_responsavel"].fillna("").astype(str) + "_"
        + df["especie"].fillna("").astype(str)
    )
    df["id_animal"] = string_temp.apply(lambda s: _gerar_hash("ANI", s))
    df.drop(columns=["string_temporaria"], inplace=True, errors="ignore")

    # Ponto 4 - Substituir strings vazias por pd.NA
    colunas_texto = [
        "email_responsavel", "nome_responsavel", "sobrenome_responsavel",
        "nome_completo", "historico", "especie", "sexo", "porte", "condicao_saude"
    ]
    for col in colunas_texto:
        df[col] = df[col].replace("", pd.NA)

    if erros_da_aba:
        mensagem_erro = "\n - ".join(erros_da_aba)
        raise ValueError(f"[SILVER] Falha na validação da aba Entradas:\n - {mensagem_erro}")
        
    log.info(f"[SILVER] Entradas: {len(df)} registos transformados com sucesso.")
    return df


# ---------------------------------------------------------------------------
#   Formulário 2 — Controle de Doações
# ---------------------------------------------------------------------------

TIPOS_DOACAO_VALIDOS = {"Dinheiro", "Ração", "Medicamentos", "Acessórios/Roupinhas"}
TIPOS_DOADOR_VALIDOS = {"Anônimo", "Identificado"}


def _validar_condicionais_doacoes(df: pd.DataFrame, erros: list[str]) -> None:
    mask_med = df["tipo_doacao"] == "Medicamentos"
    nulos_categoria = df.loc[mask_med, "categoria_medicamento"].isna().sum()
    nulos_nome_med  = df.loc[mask_med, "nome_medicamento"].isna().sum()

    if nulos_categoria > 0:
        erros.append(f"{nulos_categoria} doação(ões) de Medicamentos sem categoria informada.")
    if nulos_nome_med > 0:
        erros.append(f"{nulos_nome_med} doação(ões) de Medicamentos sem nome específico.")

    mask_din = df["tipo_doacao"] == "Dinheiro"
    nulos_valor = df.loc[mask_din, "valor_doado"].isna().sum()
    if nulos_valor > 0:
        erros.append(f"{nulos_valor} doação(ões) em Dinheiro sem valor preenchido.")

    mask_id = df["tipo_doador"] == "Identificado"
    nulos_nome = df.loc[mask_id, "nome_doador"].isna().sum()
    if nulos_nome > 0:
        erros.append(f"{nulos_nome} doador(es) Identificado(s) sem nome.")


def transformar_doacoes(df_raw: pd.DataFrame) -> pd.DataFrame:
    log.info("[SILVER] Iniciando transformação: Controle de Doações")

    df = df_raw.copy()
    erros_da_aba = []

    df.columns = df.columns.str.strip()

    # Ponto 2 - Proteção contra colunas amputadas
    COLUNAS_ESPERADAS = [
        "Carimbo de data/hora",
        "Endereço de e-mail",
        "Data da Doação",
        "Tipo de Doação",
        "Categoria do Medicamento",
        "Nome específico do Medicamento",
        "Valor Doado (R$)",
        "Tipo de Doador",
        "Nome do Doador",
    ]
    df = df.reindex(columns=COLUNAS_ESPERADAS)

    df = df.rename(columns={
        "Carimbo de data/hora":   "carimbo_ts",
        "Endereço de e-mail":     "email_doador",
        "Data da Doação":         "data_doacao",
        "Tipo de Doação":         "tipo_doacao",
        "Categoria do Medicamento": "categoria_medicamento",
        "Nome específico do Medicamento": "nome_medicamento",
        "Valor Doado (R$)":       "valor_doado",
        "Tipo de Doador":         "tipo_doador",
        "Nome do Doador":         "nome_doador",
    })

    # UTC explícito
    df["carimbo_ts"] = (
        pd.to_datetime(df["carimbo_ts"], dayfirst=True, errors="coerce")
        .dt.floor("s")
        .dt.tz_localize("UTC")
    )

    df["data_doacao"] = pd.to_datetime(
        df["data_doacao"], dayfirst=True, errors="coerce"
    ).dt.normalize()

    nulos_data = df["data_doacao"].isna().sum()
    if nulos_data > 0:
        erros_da_aba.append(f"{nulos_data} data(s) de doação inválida(s) ou em branco.")

    df["email_doador"] = df["email_doador"].astype(str).str.strip().str.lower()
    df["tipo_doacao"] = df["tipo_doacao"].astype(str).str.strip()
    df["tipo_doador"] = df["tipo_doador"].astype(str).str.strip()

    df["valor_doado"] = pd.to_numeric(df["valor_doado"], errors="coerce").astype("Float64")

    df["categoria_medicamento"] = (
        df["categoria_medicamento"].fillna("").astype(str).str.strip()
    )
    df["nome_medicamento"] = (
        df["nome_medicamento"].fillna("").astype(str).str.strip().str.title()
    )
    df["nome_doador"] = (
        df["nome_doador"].fillna("").astype(str).str.strip().str.title()
    )

    # ID de Doação (chave única)
    string_temp = (
        df["carimbo_ts"].astype(str) + "_"
        + df["tipo_doacao"].fillna("").astype(str) + "_"
        + df["valor_doado"].fillna("").astype(str)
    )
    df["id_doacao"] = string_temp.apply(lambda s: _gerar_hash("DOA", s))

    # Ponto 4 - Substituir strings vazias por pd.NA
    colunas_texto = ["email_doador", "categoria_medicamento", "nome_medicamento", "nome_doador"]
    for col in colunas_texto:
        df[col] = df[col].replace("", pd.NA)

    _validar_condicionais_doacoes(df, erros_da_aba)

    if erros_da_aba:
        mensagem_erro = "\n - ".join(erros_da_aba)
        raise ValueError(f"[SILVER] Falha na validação da aba Doações:\n - {mensagem_erro}")

    log.info(f"[SILVER] Doações: {len(df)} registros transformados com sucesso.")
    return df


# ---------------------------------------------------------------------------
#   Formulário 3 — Prontuário Médico e Rotina
# ---------------------------------------------------------------------------

CAMPOS_OBRIGATORIOS_POR_EVENTO = {
    "Medicamento": ["categoria_medicamento", "nome_medicamento"],
    "Vacina":      ["categoria_vacina", "nome_vacina"],
    "Cirurgia":    ["nome_cirurgia"],
}


def _validar_condicionais_prontuario(df: pd.DataFrame, erros: list[str]) -> None:
    for evento, campos_exigidos in CAMPOS_OBRIGATORIOS_POR_EVENTO.items():
        mask_evento = df["tipo_evento"] == evento
        
        for campo in campos_exigidos:
            vazios = df.loc[mask_evento, campo].isna().sum()
            if vazios > 0:
                erros.append(f"{vazios} registro(s) de '{evento}' sem o campo '{campo}' preenchido.")


def transformar_prontuarios(df_raw: pd.DataFrame) -> pd.DataFrame:
    log.info("[SILVER] Iniciando transformação: Prontuário Médico e Rotina")

    df = df_raw.copy()
    erros_da_aba = []
    
    df.columns = df.columns.str.strip()

    # Ponto 2 - Proteção contra colunas amputadas
    COLUNAS_ESPERADAS = [
        "Carimbo de data/hora",
        "Endereço de e-mail",
        "Data do Procedimento",
        "Nome Do Profissional",
        "Tipo de Evento",
        "Categoria do Medicamento",
        "Nome específico Medicamento",
        "Categoria da Vacina",
        "Nome específico Vacina",
        "Nome da Cirurgia realizada",
    ]
    df = df.reindex(columns=COLUNAS_ESPERADAS)

    df = df.rename(columns={
        "Carimbo de data/hora":        "carimbo_ts",
        "Endereço de e-mail":          "email_profissional",
        "Data do Procedimento":        "data_procedimento",
        "Nome Do Profissional":        "nome_profissional",
        "Tipo de Evento":              "tipo_evento",
        "Categoria do Medicamento":    "categoria_medicamento",
        "Nome específico Medicamento": "nome_medicamento",
        "Categoria da Vacina":         "categoria_vacina",
        "Nome específico Vacina":      "nome_vacina",
        "Nome da Cirurgia realizada":  "nome_cirurgia",
    })

    # UTC explícito
    df["carimbo_ts"] = (
        pd.to_datetime(df["carimbo_ts"], dayfirst=True, errors="coerce")
        .dt.floor("s")
        .dt.tz_localize("UTC")
    )

    df["data_procedimento"] = pd.to_datetime(
        df["data_procedimento"], dayfirst=True, errors="coerce"
    ).dt.normalize()

    nulos_data = df["data_procedimento"].isna().sum()
    if nulos_data > 0:
        erros_da_aba.append(f"{nulos_data} data(s) de procedimento inválida(s) ou em branco.")

    df["email_profissional"] = df["email_profissional"].astype(str).str.strip().str.lower()
    df["nome_profissional"] = df["nome_profissional"].astype(str).str.strip().str.title()
    df["tipo_evento"] = df["tipo_evento"].astype(str).str.strip()

    campos_condicionais = [
        "categoria_medicamento",
        "nome_medicamento",
        "categoria_vacina",
        "nome_vacina",
        "nome_cirurgia",
    ]
    for campo in campos_condicionais:
        df[campo] = df[campo].fillna("").astype(str).str.strip().str.title()

    # ID de Procedimento (chave única)
    string_temp = (
        df["carimbo_ts"].astype(str) + "_"
        + df["tipo_evento"].fillna("").astype(str) + "_"
        + df["nome_profissional"].fillna("").astype(str)
    )
    df["id_procedimento"] = string_temp.apply(lambda s: _gerar_hash("PROC", s))

    # Ponto 4 - Substituir strings vazias por pd.NA
    colunas_texto = campos_condicionais + ["email_profissional", "nome_profissional"]
    for col in colunas_texto:
        df[col] = df[col].replace("", pd.NA)

    _validar_condicionais_prontuario(df, erros_da_aba)

    if erros_da_aba:
        mensagem_erro = "\n - ".join(erros_da_aba)
        raise ValueError(f"[SILVER] Falha na validação da aba Prontuários:\n - {mensagem_erro}")

    log.info(f"[SILVER] Prontuários: {len(df)} registros transformados com sucesso.")
    return df


# ---------------------------------------------------------------------------
#   Formulário 4 — Registro de Adoção / Saída
# ---------------------------------------------------------------------------

MOTIVOS_COM_DESTINO = {"Adoção Definitiva", "Lar Temporário", "Transferência"}
CAMPOS_DESTINO = [
    "nome_adotante",
    "telefone",
    "cidade_destino",
    "bairro_destino",
    "num_imovel",
    "tipo_imovel",
]


def _validar_condicionais_saidas(df: pd.DataFrame, erros: list[str]) -> None:
    mask_com_destino = df["motivo_saida"].isin(MOTIVOS_COM_DESTINO)

    for campo in CAMPOS_DESTINO:
        nulos = df.loc[mask_com_destino, campo].isna().sum()
        if nulos > 0:
            mensagem = (
                f"{nulos} registro(s) com motivo que exige destino "
                f"sem o campo '{campo}' preenchido."
            )
            erros.append(mensagem)


def transformar_saidas(df_raw: pd.DataFrame) -> pd.DataFrame:
    log.info("[SILVER] Iniciando transformação: Registro de Adoção / Saída")

    df = df_raw.copy()
    erros_da_aba = []

    df.columns = df.columns.str.strip()

    # Ponto 2 - Proteção contra colunas amputadas
    COLUNAS_ESPERADAS = [
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
    ]
    df = df.reindex(columns=COLUNAS_ESPERADAS)

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

    # UTC explícito
    df["carimbo_ts"] = (
        pd.to_datetime(df["carimbo_ts"], dayfirst=True, errors="coerce")
        .dt.floor("s")
        .dt.tz_localize("UTC")
    )

    df["data_saida"] = pd.to_datetime(
        df["data_saida"], dayfirst=True, errors="coerce"
    ).dt.normalize()

    nulos_data = df["data_saida"].isna().sum()
    if nulos_data > 0:
        erros_da_aba.append(f"{nulos_data} data(s) de saída inválida(s) ou em branco.")

    df["nome_animal"] = df["nome_animal"].astype(str).str.strip().str.title()
    df["motivo_saida"] = df["motivo_saida"].astype(str).str.strip()

    for campo in ["nome_adotante", "cidade_destino", "bairro_destino"]:
        df[campo] = df[campo].fillna("").astype(str).str.strip().str.title()

    df["tipo_imovel"] = df["tipo_imovel"].fillna("").astype(str).str.strip()

    df["telefone"] = df["telefone"].apply(
        lambda x: str(int(x)) if pd.notna(x) and str(x).strip() != "" else ""
    )
    df["num_imovel"] = df["num_imovel"].apply(
        lambda x: str(int(x)) if pd.notna(x) and str(x).strip() != "" else ""
    )

    # ID de Saída (chave única)
    string_temp = (
        df["carimbo_ts"].astype(str) + "_"
        + df["nome_animal"].fillna("").astype(str) + "_"
        + df["motivo_saida"].fillna("").astype(str)
    )
    df["id_saida"] = string_temp.apply(lambda s: _gerar_hash("SAI", s))

    # Ponto 4 - Substituir strings vazias por pd.NA
    colunas_texto = CAMPOS_DESTINO + ["nome_animal", "motivo_saida"]
    for col in colunas_texto:
        df[col] = df[col].replace("", pd.NA)

    _validar_condicionais_saidas(df, erros_da_aba)

    if erros_da_aba:
        mensagem_erro = "\n - ".join(erros_da_aba)
        raise ValueError(f"[SILVER] Falha na validação da aba Saídas:\n - {mensagem_erro}")

    log.info(f"[SILVER] Saídas: {len(df)} registros transformados com sucesso.")
    return df


# ---------------------------------------------------------------------------
#   Wrapper
# ---------------------------------------------------------------------------

def transformar_dados(bronze: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    log.info("[SILVER] Iniciando transformação de todas as abas")
    silver: dict[str, pd.DataFrame] = {}

    if "entradas" in bronze:
        silver["entradas"] = transformar_entradas(bronze["entradas"])
    if "doacoes" in bronze:
        silver["doacoes"] = transformar_doacoes(bronze["doacoes"])
    if "prontuarios" in bronze:
        silver["prontuarios"] = transformar_prontuarios(bronze["prontuarios"])
    if "saidas" in bronze:
        silver["saidas"] = transformar_saidas(bronze["saidas"])

    log.info(f"[SILVER] Transformação completa — {len(silver)} abas processadas")
    return silver