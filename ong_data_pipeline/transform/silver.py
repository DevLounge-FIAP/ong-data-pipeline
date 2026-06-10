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
    
    # 1. Tipagem de Datas (tz_localize para o carimbo e normalize para a data)
    df["carimbo_ts"] = pd.to_datetime(df["carimbo_ts"], errors="coerce", dayfirst=True).dt.tz_localize("UTC")
    df["data_de_entrada"] = pd.to_datetime(df["data_de_entrada"], errors="coerce", dayfirst=True).dt.normalize()

    # 2. Alinhamento de Colunas com o schemas.py
    if "nome_completo" in df.columns:
        df.rename(columns={"nome_completo": "nome_animal"}, inplace=True)
        
    # Drop da coluna email que não precisa ir para o dash
    if "endereco_email" in df.columns:
        df.drop(columns=["endereco_email"], inplace=True)

    # 3. Engenharia de Features: Condição de Saúde (EnumList)
    df["condicao_de_saude"] = df["condicao_de_saude"].fillna("Desconhecido").astype(str)
    
    condicoes = {
        "Saudável": "saudavel", 
        "Ferido": "ferido", 
        "Doente": "doente", 
        "Desnutrido": "desnutrido"
    }
    
    for condicao_original, nome_limpo in condicoes.items():
        col_name = f"is_{nome_limpo}"
        df[col_name] = df["condicao_de_saude"].str.contains(condicao_original, case=False, na=False)

    df["flag_multiplas_condicoes"] = df[[f"is_{nome_limpo}" for nome_limpo in condicoes.values()]].sum(axis=1) > 1

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
    df["carimbo_ts"] = pd.to_datetime(df["carimbo_ts"], errors="coerce", dayfirst=True).dt.tz_localize("UTC")
    df["data_doacao"] = pd.to_datetime(df["data_doacao"], errors="coerce", dayfirst=True).dt.normalize()

    # 2. Drop de colunas não necessárias para o schema
    for col_to_drop in ["endereco_email", "endereco_de_email"]:
        if col_to_drop in df.columns:
            df.drop(columns=[col_to_drop], inplace=True)

    # 3. Tipagem Numérica (Valor doado)
    if "valor_doado" in df.columns:
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
    df["carimbo_ts"] = pd.to_datetime(df["carimbo_ts"], errors="coerce", dayfirst=True).dt.tz_localize("UTC")
    df["data_do_procedimento"] = pd.to_datetime(df["data_do_procedimento"], errors="coerce", dayfirst=True).dt.normalize()

    # 2. Drop de colunas não necessárias para o schema
    for col_to_drop in ["endereco_email", "endereco_de_email"]:
        if col_to_drop in df.columns:
            df.drop(columns=[col_to_drop], inplace=True)

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
    df["carimbo_ts"] = pd.to_datetime(df["carimbo_ts"], errors="coerce", dayfirst=True).dt.tz_localize("UTC")
    df["data_da_saida"] = pd.to_datetime(df["data_da_saida"], errors="coerce", dayfirst=True).dt.normalize()

    # 2. Drop de colunas não necessárias para o schema
    for col_to_drop in ["endereco_email", "endereco_de_email"]:
        if col_to_drop in df.columns:
            df.drop(columns=[col_to_drop], inplace=True)

    # 3. Tipagem Numérica
    if "numero_do_imovel" in df.columns:
        df["numero_do_imovel"] = pd.to_numeric(df["numero_do_imovel"], errors="coerce").astype("Int64")
    
    if "telefone_de_contato" in df.columns:
        df["telefone_de_contato"] = df["telefone_de_contato"].astype(str).str.replace(r"\D", "", regex=True)

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