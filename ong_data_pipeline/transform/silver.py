"""
Camada Silver – Limpeza, Tipagem e Transformação Inicial.

Com a migração para o AppSheet, a origem (Bronze) já garante:
1. IDs únicos nativos (id_animal, id_procedimento, etc.)
2. Integridade referencial (id_animal nas tabelas transacionais)
3. Regras de preenchimento (Obrigatoriedade e Condicionais)

O papel desta camada agora é focado em tipagem (datetime, numéricos) 
e engenharia de features (ex: flags booleanas de saúde).
"""

import logging
import pandas as pd

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
#   Funções Utilitárias
# ---------------------------------------------------------------------------

def _limpar_textos_vazios(df: pd.DataFrame) -> pd.DataFrame:
    """Substitui strings vazias ou apenas com espaços por pd.NA para o BigQuery."""
    # Aplica strip em colunas de string e substitui vazios por NA
    for col in df.select_dtypes(include=['object', 'string']).columns:
        df[col] = df[col].astype(str).str.strip().replace(["", "nan", "None"], pd.NA)
    return df

# ---------------------------------------------------------------------------
#   Transformação: Entradas
# ---------------------------------------------------------------------------

def transformar_entradas(df_bruto: pd.DataFrame) -> pd.DataFrame:
    if df_bruto.empty:
        return df_bruto

    df = df_bruto.copy()
    
    # 1. Tipagem de Datas
    df["carimbo_ts"] = pd.to_datetime(df["carimbo_ts"], errors="coerce")
    df["data_entrada"] = pd.to_datetime(df["data_entrada"], errors="coerce").dt.date

    # 2. Renomear coluna para manter compatibilidade com a Gold atual
    if "nome_animal" in df.columns:
        df.rename(columns={"nome_animal": "nome_completo"}, inplace=True)

    # 3. Engenharia de Features: Condição de Saúde (EnumList)
    # O AppSheet envia como "Ferido, Doente". transforma em flags booleanas.
    df["condicao_saude"] = df["condicao_saude"].fillna("Desconhecido").astype(str)
    
    condicoes = ["Saudável", "Ferido", "Doente", "Desnutrido"]
    for c in condicoes:
        col_name = f"is_{c.lower()}"
        # Se a string contiver a condição, é True
        df[col_name] = df["condicao_saude"].str.contains(c, case=False, na=False)

    # Flag especial para múltiplas condições (ex: Ferido E Doente)
    df["flag_multiplas_condicoes"] = df[[f"is_{c.lower()}" for c in condicoes]].sum(axis=1) > 1

    df = _limpar_textos_vazios(df)
    log.info(f"[SILVER] Entradas: {len(df)} registros transformados.")
    return df

# ---------------------------------------------------------------------------
#   Transformação: Doações
# ---------------------------------------------------------------------------

def transformar_doacoes(df_bruto: pd.DataFrame) -> pd.DataFrame:
    if df_bruto.empty:
        return df_bruto

    df = df_bruto.copy()

    # 1. Tipagem de Datas
    df["carimbo_ts"] = pd.to_datetime(df["carimbo_ts"], errors="coerce")
    df["data_doacao"] = pd.to_datetime(df["data_doacao"], errors="coerce").dt.date

    # 2. Tipagem Numérica (Valor doado)
    if "valor_doado" in df.columns:
        # Remove caracteres indesejados caso existam e converte para numérico
        df["valor_doado"] = pd.to_numeric(
            df["valor_doado"].astype(str).str.replace(r"[^\d.]", "", regex=True), 
            errors="coerce"
        )

    df = _limpar_textos_vazios(df)
    log.info(f"[SILVER] Doações: {len(df)} registros transformados.")
    return df

# ---------------------------------------------------------------------------
#   Transformação: Prontuários
# ---------------------------------------------------------------------------

def transformar_prontuarios(df_bruto: pd.DataFrame) -> pd.DataFrame:
    if df_bruto.empty:
        return df_bruto

    df = df_bruto.copy()

    # 1. Tipagem de Datas
    df["carimbo_ts"] = pd.to_datetime(df["carimbo_ts"], errors="coerce")
    df["data_procedimento"] = pd.to_datetime(df["data_procedimento"], errors="coerce").dt.date

    df = _limpar_textos_vazios(df)
    log.info(f"[SILVER] Prontuários: {len(df)} registros transformados.")
    return df

# ---------------------------------------------------------------------------
#   Transformação: Saídas
# ---------------------------------------------------------------------------

def transformar_saidas(df_bruto: pd.DataFrame) -> pd.DataFrame:
    if df_bruto.empty:
        return df_bruto

    df = df_bruto.copy()

    # 1. Tipagem de Datas
    df["carimbo_ts"] = pd.to_datetime(df["carimbo_ts"], errors="coerce")
    df["data_saida"] = pd.to_datetime(df["data_saida"], errors="coerce").dt.date

    # 2. Tipagem Numérica
    if "num_imovel" in df.columns:
        df["num_imovel"] = pd.to_numeric(df["num_imovel"], errors="coerce").astype("Int64")
    
    # Telefone como string (limpando apenas caracteres) para evitar notação científica
    if "telefone_adotante" in df.columns:
        df["telefone_adotante"] = df["telefone_adotante"].astype(str).str.replace(r"\D", "", regex=True)

    df = _limpar_textos_vazios(df)
    log.info(f"[SILVER] Saídas: {len(df)} registros transformados.")
    return df

# ---------------------------------------------------------------------------
#   Wrapper Global
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

    log.info("[SILVER] Transformação concluída com sucesso.")
    return silver