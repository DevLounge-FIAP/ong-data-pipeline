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
    "animal silvestres": "Animal Silvestre",
    "outro":             "Outro",
}

CONDICAO_VALIDA = {"Saudável", "Ferido", "Doente", "Desnutrido", "Desconhecido"}


def _normalizar_condicao(valor: str) -> str:
    partes = [p.strip().title() for p in valor.split(",")]
    validas   = [p for p in partes if p in CONDICAO_VALIDA]
    invalidas = [p for p in partes if p not in CONDICAO_VALIDA]
    if invalidas:
        log.warning(f"[SILVER] Condição de saúde não reconhecida: {invalidas} → ignorada")
    return ", ".join(validas) if validas else "Desconhecido"

'''
def transformar_entradas(df_raw: pd.DataFrame) -> pd.DataFrame:
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

    df["carimbo_ts"]   = pd.to_datetime(df["carimbo_ts"], errors="coerce").dt.floor("s")
    df["data_entrada"] = pd.to_datetime(df["data_entrada"], errors="coerce").dt.date

    df["email_responsavel"] = df["email_responsavel"].astype(str).str.strip().str.lower()

    df = _strip_texto(df, ["nome_responsavel", "sobrenome_responsavel"])
    df["nome_completo_responsavel"] = (
        df["nome_responsavel"] + " " + df["sobrenome_responsavel"]
    ).str.strip()

    df["especie"] = (
        df["especie"]
        .astype(str).str.strip().str.lower()
        .map(MAPA_ESPECIE)
        .fillna("Outro")
    )

    df["sexo"]  = df["sexo"].astype(str).str.strip()
    df["porte"] = df["porte"].astype(str).str.strip()

    df["condicao_saude"] = (
        df["condicao_saude"]
        .astype(str).str.strip()
        .str.replace("Saúdavel", "Saudável", regex=False)
        .apply(_normalizar_condicao)
    )
    df["flag_multiplas_condicoes"] = df["condicao_saude"].str.contains(",").astype(int)

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
'''
#----------------------------------
# Parte do Bruno
#----------------------------------
def transformar_saidas(df_raw: pd.DataFrame) -> pd.DataFrame:
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

    df["carimbo_ts"] = pd.to_datetime(df["carimbo_ts"], errors="coerce").dt.floor("s")
    df["data_saida"] = pd.to_datetime(df["data_saida"], errors="coerce").dt.date

    df = _strip_texto(df, [
        "nome_animal", "motivo_saida", "nome_adotante",
        "cidade_destino", "bairro_destino", "tipo_imovel",
    ])

    df = _id_para_string(df, ["telefone", "num_imovel"])

    log.info(f"[SILVER] Saídas: {len(df)} registros transformados")
    return df


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

#----------------------------------
# Minha parte ainda fazendo e testando (Aelton)
#----------------------------------
def transformar_prontuarios(df_raw: pd.DataFrame) -> pd.DataFrame:
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

    df["carimbo_ts"] = pd.to_datetime(df["carimbo_ts"], errors="coerce").dt.floor("s")
    df["data_procedimento"] = pd.to_datetime(
        df["data_procedimento"], dayfirst=True, errors="coerce"
    ).dt.date

    nulos_data = df["data_procedimento"].isna().sum()
    if nulos_data > 0:
        log.warning(f"[SILVER] {nulos_data} data(s) de procedimento inválida(s) → NaT")

    df["email_profissional"] = df["email_profissional"].astype(str).str.strip().str.lower()

    df["tipo_evento"] = (
        df["tipo_evento"]
        .astype(str).str.strip().str.lower()
        .map(MAPA_TIPO_EVENTO) # Ver para ajustar ainda, não vai precisar de mapa eu acho
        .fillna("Não Informado")
    )

    df = _strip_texto(df, ["nome_profissional"])

    df = _opcional_para_string(df, [
        "categoria_medicamento", "nome_medicamento",
        "categoria_vacina", "nome_vacina",
        "nome_cirurgia",
    ])

    log.info(f"[SILVER] Prontuários: {len(df)} registros transformados")
    return df

'''
def transformar_doacoes(df_raw: pd.DataFrame) -> pd.DataFrame:
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

    df["carimbo_ts"]  = pd.to_datetime(df["carimbo_ts"], errors="coerce").dt.floor("s")
    df["data_doacao"] = pd.to_datetime(df["data_doacao"], errors="coerce").dt.date

    df["email_doador"] = df["email_doador"].astype(str).str.strip().str.lower()

    df["tipo_doacao"] = df["tipo_doacao"].astype(str).str.strip()
    df["tipo_doador"] = df["tipo_doador"].astype(str).str.strip()

    df["valor_doado"] = df["valor_doado"].fillna(0.0).astype(float).round(2)

    df["nome_doador"] = (
        df["nome_doador"].fillna("").astype(str).str.strip().str.title()
    )

    df = _opcional_para_string(df, ["categoria_medicamento", "nome_especifico_item"])

    log.info(f"[SILVER] Doações: {len(df)} registros transformados")
    return df

'''
def transformar_dados(bronze: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Wrapper que transforma todas as abas da camada bronze para silver."""
    esperadas = ["entradas", "saidas", "prontuarios", "doacoes"]
    missing = [k for k in esperadas if k not in bronze]
    if missing:
        raise KeyError(f"Chaves ausentes na camada bronze: {missing}")

    silver = {}
    #silver["entradas"] = transformar_entradas(bronze["entradas"]) if not bronze["entradas"].empty else bronze["entradas"]
    silver["saidas"] = transformar_saidas(bronze["saidas"]) if not bronze["saidas"].empty else bronze["saidas"]
    silver["prontuarios"] = transformar_prontuarios(bronze["prontuarios"]) if not bronze["prontuarios"].empty else bronze["prontuarios"]
    #silver["doacoes"] = transformar_doacoes(bronze["doacoes"]) if not bronze["doacoes"].empty else bronze["doacoes"]

    return silver
