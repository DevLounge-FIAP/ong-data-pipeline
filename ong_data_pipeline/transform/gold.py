"""
Camada Gold – Métricas, Indicadores e Agregações.

Toda regra de negócio e toda agregação deve residir aqui.
Os dados de entrada são os DataFrames da camada Silver já validados.
"""

import pandas as pd
import logging

log = logging.getLogger(__name__)


def gerar_dim_calendario(data_min: pd.Timestamp, data_max: pd.Timestamp) -> pd.DataFrame:
    """
    Cria uma dimensão calendário entre a menor e a maior data do domínio.
    Essencial para filtros temporais consistentes no Looker Studio.
    """
    if pd.isna(data_min) or pd.isna(data_max):
        raise ValueError("Datas limite inválidas para gerar dim_calendario.")

    datas = pd.date_range(start=data_min, end=data_max, freq="D")
    df_cal = pd.DataFrame({"data": datas})
    df_cal["ano"] = df_cal["data"].dt.year
    df_cal["mes"] = df_cal["data"].dt.month
    df_cal["nome_mes"] = df_cal["data"].dt.strftime("%B")
    df_cal["trimestre"] = df_cal["data"].dt.quarter
    df_cal["dia_da_semana"] = df_cal["data"].dt.day_name()
    return df_cal


def gerar_gold_entradas(df_entradas: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega entradas de animais por ano/mês + características.
    """
    cols_obrigatorias = [
        "data_entrada", "id_animal",
        "is_saudavel", "is_ferido", "is_doente", "is_desnutrido", "is_desconhecido",
        "especie", "sexo", "porte", "condicao_saude",
    ]
    for col in cols_obrigatorias:
        if col not in df_entradas.columns:
            raise KeyError(f"Coluna obrigatória ausente em entradas: {col}")

    df = df_entradas.copy()
    df["data_entrada"] = pd.to_datetime(df["data_entrada"])
    df["ano"] = df["data_entrada"].dt.year
    df["mes"] = df["data_entrada"].dt.month

    agg = df.groupby(["ano", "mes", "especie", "sexo", "porte", "condicao_saude"]).agg(
        total_entradas=("id_animal", "count"),
        quantidade_saudaveis=("is_saudavel", "sum"),
        quantidade_feridos=("is_ferido", "sum"),
        quantidade_doentes=("is_doente", "sum"),
        quantidade_desnutridos=("is_desnutrido", "sum"),
        quantidade_desconhecido=("is_desconhecido", "sum"),
    ).reset_index()

    # Garantir inteiros (soma de booleanos com na=False não gera NaN)
    colunas_int = ["quantidade_saudaveis", "quantidade_feridos", "quantidade_doentes",
                   "quantidade_desnutridos", "quantidade_desconhecido"]
    agg[colunas_int] = agg[colunas_int].fillna(0).astype(int)
    agg["total_entradas"] = agg["total_entradas"].astype(int)

    return agg


def gerar_gold_doacoes(df_doacoes: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega doações por ano/mês, tipo de doação e tipo de doador.
    """
    cols_obrigatorias = [
        "data_doacao", "tipo_doacao", "tipo_doador", "valor_doado"
    ]
    for col in cols_obrigatorias:
        if col not in df_doacoes.columns:
            raise KeyError(f"Coluna obrigatória ausente em doações: {col}")

    df = df_doacoes.copy()
    df["data_doacao"] = pd.to_datetime(df["data_doacao"])
    df["ano"] = df["data_doacao"].dt.year
    df["mes"] = df["data_doacao"].dt.month

    agg = df.groupby(["ano", "mes", "tipo_doacao", "tipo_doador"]).agg(
        total_doacoes=("tipo_doacao", "count"),
        soma_valor_doado=("valor_doado", "sum"),
        media_valor_doado=("valor_doado", "mean"),
    ).reset_index()

    # Ajuste de tipos
    agg["total_doacoes"] = agg["total_doacoes"].astype(int)
    # soma e média já são float; manter FLOAT no BigQuery
    return agg


def gerar_gold_prontuarios(df_prontuarios: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega procedimentos por ano/mês, tipo de evento e profissional.
    """
    cols_obrigatorias = [
        "data_procedimento", "tipo_evento", "nome_profissional"
    ]
    for col in cols_obrigatorias:
        if col not in df_prontuarios.columns:
            raise KeyError(f"Coluna obrigatória ausente em prontuários: {col}")

    df = df_prontuarios.copy()
    df["data_procedimento"] = pd.to_datetime(df["data_procedimento"])
    df["ano"] = df["data_procedimento"].dt.year
    df["mes"] = df["data_procedimento"].dt.month

    agg = df.groupby(["ano", "mes", "tipo_evento", "nome_profissional"]).agg(
        total_procedimentos=("tipo_evento", "count"),
    ).reset_index()

    agg["total_procedimentos"] = agg["total_procedimentos"].astype(int)
    return agg


def gerar_gold_saidas(df_saidas: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega saídas por ano/mês, motivo e destino.
    """
    cols_obrigatorias = [
        "data_saida", "motivo_saida", "cidade_destino", "bairro_destino"
    ]
    for col in cols_obrigatorias:
        if col not in df_saidas.columns:
            raise KeyError(f"Coluna obrigatória ausente em saídas: {col}")

    df = df_saidas.copy()
    df["data_saida"] = pd.to_datetime(df["data_saida"])
    df["ano"] = df["data_saida"].dt.year
    df["mes"] = df["data_saida"].dt.month

    agg = df.groupby(["ano", "mes", "motivo_saida", "cidade_destino", "bairro_destino"]).agg(
        total_saidas=("motivo_saida", "count"),
    ).reset_index()

    agg["total_saidas"] = agg["total_saidas"].astype(int)
    return agg


def transformar_gold(silver_dfs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """
    Orquestrador da camada Gold. Recebe um dicionário com as tabelas Silver
    já carregadas (ex.: 'entradas', 'doacoes', 'prontuarios', 'saidas')
    e retorna um dicionário com todas as tabelas Gold prontas para carga.

    Princípio fail‑fast: qualquer ausência de tabela ou coluna interrompe o processo.
    """
    log.info("[GOLD] Iniciando transformação da camada Gold.")

    tabelas_esperadas = {"entradas", "doacoes", "prontuarios", "saidas"}
    for tabela in tabelas_esperadas:
        if tabela not in silver_dfs:
            raise ValueError(f"[GOLD] Tabela Silver '{tabela}' não encontrada. Abortando.")

    gold: dict[str, pd.DataFrame] = {}

    # 1. Gerar métricas de entradas
    log.info("[GOLD] Gerando gold_entradas_metricas...")
    gold["gold_entradas_metricas"] = gerar_gold_entradas(silver_dfs["entradas"])

    # 2. Gerar métricas de doações
    log.info("[GOLD] Gerando gold_doacoes_metricas...")
    gold["gold_doacoes_metricas"] = gerar_gold_doacoes(silver_dfs["doacoes"])

    # 3. Gerar métricas de prontuários
    log.info("[GOLD] Gerando gold_prontuarios_metricas...")
    gold["gold_prontuarios_metricas"] = gerar_gold_prontuarios(silver_dfs["prontuarios"])

    # 4. Gerar métricas de saídas
    log.info("[GOLD] Gerando gold_saidas_metricas...")
    gold["gold_saidas_metricas"] = gerar_gold_saidas(silver_dfs["saidas"])

    # 5. Gerar dim_calendario com base nas datas de todas as tabelas
    log.info("[GOLD] Gerando dim_calendario...")
    datas = []
    for df in silver_dfs.values():
        for col in df.columns:
            if col.startswith("data_"):
                datas.append(pd.to_datetime(df[col].dropna()))
    if not datas:
        raise ValueError("[GOLD] Nenhuma data disponível para gerar dim_calendario.")
    todas_datas = pd.concat(datas)
    gold["dim_calendario"] = gerar_dim_calendario(todas_datas.min(), todas_datas.max())

    log.info("[GOLD] Transformação Gold concluída com sucesso.")
    return gold