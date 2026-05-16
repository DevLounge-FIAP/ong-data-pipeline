import logging
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#   Utilitários internos
# ---------------------------------------------------------------------------

def _strip_texto(df: pd.DataFrame, colunas: list) -> pd.DataFrame:
    """Strip + title case em colunas de texto livre."""
    for col in colunas:
        df[col] = df[col].astype(str).str.strip().str.title()
    return df


def _opcional_para_string(df: pd.DataFrame, colunas: list) -> pd.DataFrame:
    """Campos opcionais: NaN → string vazia, depois strip + title case."""
    for col in colunas:
        df[col] = df[col].fillna("").astype(str).str.strip().str.title()
    return df


def _id_para_string(df: pd.DataFrame, colunas: list) -> pd.DataFrame:
    """
    Converte int64 para string sem o '.0' que astype(str) adiciona.
    Usado em telefone e nº de imóvel — identificadores, não métricas.
    """
    for col in colunas:
        df[col] = df[col].apply(
            lambda x: str(int(x)) if pd.notna(x) and str(x).strip() != "" else ""
        )
    return df


# ---------------------------------------------------------------------------
#   Entrada / Novo Resgate
# ---------------------------------------------------------------------------

MAPA_ESPECIE = {
    "cão":               "Cão",
    "cao":               "Cão",
    "cachorro":          "Cão",
    "gato":              "Gato",
    "ave":               "Ave",
    "réptil":            "Réptil",
    "reptil":            "Réptil",
    "roedor":            "Roedor",
    "suíno":             "Suíno",
    "suino":             "Suíno",
    "bovino":            "Bovino",
    "equino":            "Equino",
    "pet exótico":       "Pet Exótico",
    "pet exotico":       "Pet Exótico",
    "animal silvestre":  "Animal Silvestre",
    "animal silvestres": "Animal Silvestre",  # erro de digitação real nos dados
    "outro":             "Outro",
}

CONDICAO_VALIDA = {"Saudável", "Ferido", "Doente", "Desnutrido", "Desconhecido"}


def _normalizar_condicao(valor: str) -> str:
    """
    Condição de Saúde aceita múltipla seleção no Forms → "Ferido, Doente".
    Normaliza cada valor individualmente e reconstrói a string.
    """
    partes = [p.strip().title() for p in valor.split(",")]
    validas   = [p for p in partes if p in CONDICAO_VALIDA]
    invalidas = [p for p in partes if p not in CONDICAO_VALIDA]
    if invalidas:
        log.warning(f"[SILVER] Condição de saúde não reconhecida: {invalidas} → ignorada")
    return ", ".join(validas) if validas else "Desconhecido"


def transformar_entradas(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Bronze → Silver: Entrada / Novo Resgate

    Problemas reais tratados:
      - Nomes de colunas com espaços extras
      - "Animal silvestres" (erro de digitação no Forms) → "Animal Silvestre"
      - "Saúdavel" (acento errado) → corrigido antes do mapa
      - Condição de Saúde multi-valor: "Ferido, Doente" → preservado e validado
      - Histórico com \\n literal vindo do Forms
      - Trailing spaces em nome e sobrenome do responsável
    """
    log.info("[SILVER] Iniciando transformação: Entrada / Novo Resgate")

    df = df_raw.copy()
    df.columns = df.columns.str.strip()

    colunas_selecionadas = [
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
    df = df[colunas_selecionadas].copy()

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

    # Datas
    df["carimbo_ts"]   = pd.to_datetime(df["carimbo_ts"], errors="coerce").dt.floor("s")
    df["data_entrada"] = pd.to_datetime(df["data_entrada"], errors="coerce").dt.date

    # E-mail
    df["email_responsavel"] = df["email_responsavel"].astype(str).str.strip().str.lower()

    # Nome e sobrenome — strip + title case, depois montar nome completo
    df = _strip_texto(df, ["nome_responsavel", "sobrenome_responsavel"])
    df["nome_completo_responsavel"] = (
        df["nome_responsavel"] + " " + df["sobrenome_responsavel"]
    ).str.strip()

    # Espécie — normaliza via mapa (cobre erros históricos de digitação)
    df["especie"] = (
        df["especie"]
        .astype(str).str.strip().str.lower()
        .map(MAPA_ESPECIE)
        .fillna("Outro")
    )

    # Sexo e Porte — dropdown garante valor, só strip
    df["sexo"]  = df["sexo"].astype(str).str.strip()
    df["porte"] = df["porte"].astype(str).str.strip()

    # Condição de Saúde — corrige acento errado real, depois normaliza multi-valor
    df["condicao_saude"] = (
        df["condicao_saude"]
        .astype(str).str.strip()
        .str.replace("Saúdavel", "Saudável", regex=False)
        .apply(_normalizar_condicao)
    )
    df["flag_multiplas_condicoes"] = df["condicao_saude"].str.contains(",").astype(int)

    # Histórico — remove \n literal do Forms e normaliza espaços
    df["historico"] = (
        df["historico"]
        .astype(str)
        .str.replace(r"\\n", " ", regex=True)
        .str.replace(r"\n",  " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    log.info(f"[SILVER] Entradas: {len(df)} registros transformados")
    return df


# ---------------------------------------------------------------------------
#   Registro de Adoção / Saída
# ---------------------------------------------------------------------------

def transformar_saidas(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Bronze → Silver: Registro de Adoção / Saída

    Problemas reais tratados:
      - Nomes de colunas com espaços extras ("  Motivo da Saída  ")
      - Telefone e Nº do Imóvel como int64 → string (identificadores, não métricas)
      - Trailing spaces em cidades, bairros e nomes
      - Data da Saída já vem como datetime64 do Sheets
    """
    log.info("[SILVER] Iniciando transformação: Registro de Adoção / Saída")

    df = df_raw.copy()
    df.columns = df.columns.str.strip()

    colunas_selecionadas = [
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
    df = df[colunas_selecionadas].copy()

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

    # Datas
    df["carimbo_ts"] = pd.to_datetime(df["carimbo_ts"], errors="coerce").dt.floor("s")
    df["data_saida"] = pd.to_datetime(df["data_saida"], errors="coerce").dt.date

    # Texto livre
    df = _strip_texto(df, [
        "nome_animal", "motivo_saida", "nome_adotante",
        "cidade_destino", "bairro_destino", "tipo_imovel",
    ])

    # Identificadores numéricos → string limpa
    df = _id_para_string(df, ["telefone", "num_imovel"])

    log.info(f"[SILVER] Saídas: {len(df)} registros transformados")
    return df


# ---------------------------------------------------------------------------
#   Prontuário Médico e Rotina
# ---------------------------------------------------------------------------

MAPA_TIPO_EVENTO = {
    "vacina":               "Vacinação",
    "vacinação":            "Vacinação",
    "consulta":             "Consulta",
    "consulta veterinária": "Consulta",
    "consulta de rotina":   "Consulta",
    "cirurgia":             "Cirurgia",
    "vermifugo":            "Vermífugo",
    "vermífugo":            "Vermífugo",
    "medicamento":          "Medicamento",
}


def transformar_prontuarios(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Bronze → Silver: Prontuário Médico e Rotina

    Problemas reais tratados:
      - Colunas "Nome específico Medicamento" e "Nome específico" (vacina)
        agora têm nomes distintos — sem ambiguidade nessa versão
      - Tipo de Evento com variações de case/escrita → normalizado via mapa
      - Campos opcionais (medicamento, cirurgia) chegam como NaN → string vazia
      - Trailing spaces no nome da vacina
      - Data do Procedimento já vem como datetime64 do Sheets
    """
    log.info("[SILVER] Iniciando transformação: Prontuário Médico e Rotina")

    df = df_raw.copy()
    df.columns = df.columns.str.strip()

    colunas_selecionadas = [
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
    ]
    df = df[colunas_selecionadas].copy()

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

    # Datas
    df["carimbo_ts"] = pd.to_datetime(df["carimbo_ts"], errors="coerce").dt.floor("s")
    df["data_procedimento"] = pd.to_datetime(
        df["data_procedimento"], dayfirst=True, errors="coerce"
    ).dt.date

    nulos_data = df["data_procedimento"].isna().sum()
    if nulos_data > 0:
        log.warning(f"[SILVER] {nulos_data} data(s) de procedimento inválida(s) → NaT")

    # E-mail
    df["email_profissional"] = df["email_profissional"].astype(str).str.strip().str.lower()

    # Tipo de Evento — normaliza variações de digitação e case
    df["tipo_evento"] = (
        df["tipo_evento"]
        .astype(str).str.strip().str.lower()
        .map(MAPA_TIPO_EVENTO)
        .fillna("Não Informado")
    )

    # Nome do profissional — obrigatório
    df = _strip_texto(df, ["nome_profissional"])

    # Campos opcionais — dependem do tipo de evento
    df = _opcional_para_string(df, [
        "categoria_medicamento", "nome_medicamento",
        "categoria_vacina", "nome_vacina",
        "nome_cirurgia",
    ])

    log.info(f"[SILVER] Prontuários: {len(df)} registros transformados")
    return df


# ---------------------------------------------------------------------------
#   Controle de Doações
# ---------------------------------------------------------------------------

def transformar_doacoes(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Bronze → Silver: Controle de Doações

    Problemas reais tratados:
      - Nomes de colunas com espaços extras ("  Tipo de Doação  ")
      - Valor Doado como float64 — NaN para doações de itens (ração, acessórios)
        que não têm valor monetário → preencher com 0.0
      - Nome do Doador com trailing spaces ("Brunin Volks Wagen ")
      - Nome do Doador NaN quando Tipo Doador = "Anônimo" → comportamento esperado
      - Nome específico do item com espaços excessivos ("Antipulgas XUV       ")
      - Categoria do Medicamento e Nome específico NaN para doações não-medicamento
    """
    log.info("[SILVER] Iniciando transformação: Controle de Doações")

    df = df_raw.copy()
    df.columns = df.columns.str.strip()

    colunas_selecionadas = [
        "Carimbo de data/hora",
        "Endereço de e-mail",
        "Data da Doação",
        "Tipo de Doação",
        "Categoria do Medicamento",
        "Nome específico",
        "Valor Doado (R$)",
        "Tipo de Doador",
        "Nome do Doador",
    ]
    df = df[colunas_selecionadas].copy()

    df = df.rename(columns={
        "Carimbo de data/hora":   "carimbo_ts",
        "Endereço de e-mail":     "email_doador",
        "Data da Doação":         "data_doacao",
        "Tipo de Doação":         "tipo_doacao",
        "Categoria do Medicamento": "categoria_medicamento",
        "Nome específico":        "nome_especifico_item",
        "Valor Doado (R$)":       "valor_doado",
        "Tipo de Doador":         "tipo_doador",
        "Nome do Doador":         "nome_doador",
    })

    # Datas
    df["carimbo_ts"]  = pd.to_datetime(df["carimbo_ts"], errors="coerce").dt.floor("s")
    df["data_doacao"] = pd.to_datetime(df["data_doacao"], errors="coerce").dt.date

    # E-mail
    df["email_doador"] = df["email_doador"].astype(str).str.strip().str.lower()

    # Dropdowns — só strip
    df["tipo_doacao"] = df["tipo_doacao"].astype(str).str.strip()
    df["tipo_doador"] = df["tipo_doador"].astype(str).str.strip()

    # Valor Doado — doações de itens não têm valor monetário → 0.0
    df["valor_doado"] = df["valor_doado"].fillna(0.0).astype(float).round(2)

    # Nome do Doador — NaN para anônimos é esperado → string vazia
    df["nome_doador"] = (
        df["nome_doador"].fillna("").astype(str).str.strip().str.title()
    )

    # Campos opcionais do item doado
    df = _opcional_para_string(df, ["categoria_medicamento", "nome_especifico_item"])

    log.info(f"[SILVER] Doações: {len(df)} registros transformados")
    return df


# ---------------------------------------------------------------------------
#   Parte para chamar no main,py
# ---------------------------------------------------------------------------

def transformar_dados(dados_bronze: dict) -> dict:
    """
    Recebe o dicionário de DataFrames brutos vindo do extract.py
    e retorna o dicionário de DataFrames Silver transformados.

    Uso no main.py:
        from extract import extrair_dados_bronze
        from transform import transformar_dados

        bronze = extrair_dados_bronze()
        silver = transformar_dados(bronze)
    """
    return {
        "entradas":    transformar_entradas(dados_bronze["entradas"]),
        "saidas":      transformar_saidas(dados_bronze["saidas"]),
        "prontuarios": transformar_prontuarios(dados_bronze["prontuarios"]),
        "doacoes":     transformar_doacoes(dados_bronze["doacoes"]),
    }


# ---------------------------------------------------------------------------
#   Teste local (sem banco, sem gspread)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    file = sys.argv[1] if len(sys.argv) > 1 else "PipelineV2.xlsx"

    bronze = {
        "entradas":    pd.read_excel(file, sheet_name="Entrada  Novo Resgate"),
        "saidas":      pd.read_excel(file, sheet_name="Registro de Adoção  Saída"),
        "prontuarios": pd.read_excel(file, sheet_name="Prontuário Médico e Rotina"),
        "doacoes":     pd.read_excel(file, sheet_name="Controle de Doações"),
    }

    silver = transformar_dados(bronze)

    for nome, df in silver.items():
        print(f"\n{'='*60}")
        print(f"Silver → {nome}  ({len(df)} registros)")
        print(df.to_string(index=False))
        print(f"\nDtypes:\n{df.dtypes}")