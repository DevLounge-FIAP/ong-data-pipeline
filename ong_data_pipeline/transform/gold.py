"""
Camada Gold – Métricas, Indicadores e Agregações (One Big Table).

Toda regra de negócio e toda agregação devem residir aqui.
Os dados de entrada são os DataFrames da camada Silver já validados.
"""

import pandas as pd
import logging

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


# ---------------------------------------------------------------------------
# Dimensão Calendário Mensal
# ---------------------------------------------------------------------------
def gerar_dim_calendario_mensal(data_min: pd.Timestamp, data_max: pd.Timestamp) -> pd.DataFrame:
    """
    Cria uma dimensão calendário mensal (ano_mês) cobrindo todo o intervalo,
    com nomes de meses em português.
    """
    if pd.isna(data_min) or pd.isna(data_max):
        raise ValueError("Datas limite inválidas para gerar dim_calendario.")

    # Garantir que data_min e data_max estejam no primeiro e último dia do mês
    data_min = data_min.replace(day=1)
    # Para o último mês, usar o primeiro dia do mês seguinte e depois voltar (para pegar o mês completo)
    data_max = data_max.replace(day=1) + pd.DateOffset(months=1) - pd.DateOffset(days=1)

    datas_mensais = pd.date_range(start=data_min, end=data_max, freq="MS")  # Month Start
    df_cal = pd.DataFrame({"data": datas_mensais})
    df_cal["ano"] = df_cal["data"].dt.year
    df_cal["mes"] = df_cal["data"].dt.month
    df_cal["ano_mes"] = df_cal["data"].dt.strftime("%Y-%m")
    df_cal["nome_mes"] = df_cal["mes"].map(MESES_PT)
    df_cal["trimestre"] = df_cal["data"].dt.quarter
    df_cal["ano_mes_num"] = df_cal["ano"] * 100 + df_cal["mes"]
    return df_cal


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------
def _adicionar_ano_mes(df: pd.DataFrame, coluna_data: str) -> pd.DataFrame:
    """Adiciona colunas 'ano', 'mes' e 'ano_mes' a partir de uma coluna de data."""
    df = df.copy()
    serie_data = pd.to_datetime(df[coluna_data])
    df["ano"] = serie_data.dt.year
    df["mes"] = serie_data.dt.month
    df["ano_mes"] = serie_data.dt.strftime("%Y-%m")
    return df


# ---------------------------------------------------------------------------
# Tabelas OBT (One Big Table)
# ---------------------------------------------------------------------------
def gerar_gold_entradas(df_entradas: pd.DataFrame) -> pd.DataFrame:
    """
    Tabela OBT de entradas: dimensões + métricas já unidas.
    Remove a redundância das flags de condição.
    """
    cols_obrigatorias = [
        "data_entrada", "id_animal", "especie", "sexo", "porte", "condicao_saude"
    ]
    for col in cols_obrigatorias:
        if col not in df_entradas.columns:
            raise KeyError(f"Coluna obrigatória ausente em entradas: {col}")

    df = _adicionar_ano_mes(df_entradas, "data_entrada")

    agg = df.groupby(["ano", "mes", "ano_mes", "especie", "sexo", "porte", "condicao_saude"]).agg(
        total_entradas=("id_animal", "count"),
    ).reset_index()

    agg["total_entradas"] = agg["total_entradas"].astype(int)
    return agg


def gerar_gold_doacoes(df_doacoes: pd.DataFrame) -> pd.DataFrame:
    """
    Tabela OBT de doações: inclui maior e menor doação.
    """
    cols_obrigatorias = [
        "data_doacao", "tipo_doacao", "tipo_doador", "valor_doado"
    ]
    for col in cols_obrigatorias:
        if col not in df_doacoes.columns:
            raise KeyError(f"Coluna obrigatória ausente em doações: {col}")

    df = _adicionar_ano_mes(df_doacoes, "data_doacao")

    agg = df.groupby(["ano", "mes", "ano_mes", "tipo_doacao", "tipo_doador"]).agg(
        total_doacoes=("tipo_doacao", "count"),
        soma_valor_doado=("valor_doado", "sum"),
        media_valor_doado=("valor_doado", "mean"),
        maior_doacao=("valor_doado", "max"),
        menor_doacao=("valor_doado", "min"),
    ).reset_index()

    agg["total_doacoes"] = agg["total_doacoes"].astype(int)
    return agg


def gerar_gold_prontuarios(df_prontuarios: pd.DataFrame) -> pd.DataFrame:
    """
    Tabela OBT de procedimentos.
    """
    cols_obrigatorias = [
        "data_procedimento", "tipo_evento", "nome_profissional"
    ]
    for col in cols_obrigatorias:
        if col not in df_prontuarios.columns:
            raise KeyError(f"Coluna obrigatória ausente em prontuários: {col}")

    df = _adicionar_ano_mes(df_prontuarios, "data_procedimento")

    agg = df.groupby(["ano", "mes", "ano_mes", "tipo_evento", "nome_profissional"]).agg(
        total_procedimentos=("tipo_evento", "count"),
    ).reset_index()

    agg["total_procedimentos"] = agg["total_procedimentos"].astype(int)
    return agg


def gerar_gold_saidas(df_saidas: pd.DataFrame) -> pd.DataFrame:
    """
    Tabela OBT de saídas.
    """
    cols_obrigatorias = [
        "data_saida", "motivo_saida", "cidade_destino", "bairro_destino"
    ]
    for col in cols_obrigatorias:
        if col not in df_saidas.columns:
            raise KeyError(f"Coluna obrigatória ausente em saídas: {col}")

    df = _adicionar_ano_mes(df_saidas, "data_saida")

    agg = df.groupby(["ano", "mes", "ano_mes", "motivo_saida", "cidade_destino", "bairro_destino"]).agg(
        total_saidas=("motivo_saida", "count"),
    ).reset_index()

    agg["total_saidas"] = agg["total_saidas"].astype(int)
    return agg


def gerar_gold_animais_mensal(
    df_entradas: pd.DataFrame, df_saidas: pd.DataFrame, dim_mensal: pd.DataFrame
) -> pd.DataFrame:
    """
    Cria a tabela de saldo mensal de animais, garantindo meses sem eventos (zeros)
    e calculando o saldo acumulado.
    """
    # Agrega entradas por ano_mes
    entradas_agg = _adicionar_ano_mes(df_entradas, "data_entrada")
    entradas_agg = entradas_agg.groupby("ano_mes").agg(
        total_entradas=("id_animal", "count")
    ).reset_index()

    # Agrega saídas por ano_mes
    saidas_agg = _adicionar_ano_mes(df_saidas, "data_saida")
    saidas_agg = saidas_agg.groupby("ano_mes").agg(
        total_saidas=("id_saida", "count")
    ).reset_index()

    # Merge com a dimensão calendário mensal (garante todos os meses)
    base = dim_mensal[["ano_mes"]].copy()
    base = base.merge(entradas_agg, on="ano_mes", how="left")
    base = base.merge(saidas_agg, on="ano_mes", how="left")

    # Preenche NaN com 0
    base["total_entradas"] = base["total_entradas"].fillna(0).astype(int)
    base["total_saidas"] = base["total_saidas"].fillna(0).astype(int)

    # Calcula saldo acumulado
    base["saldo_liquido"] = base["total_entradas"] - base["total_saidas"]
    base["saldo_acumulado"] = base["saldo_liquido"].cumsum()

    # Adiciona informações temporais
    base = base.merge(dim_mensal[["ano_mes", "ano", "mes", "nome_mes", "trimestre"]], on="ano_mes", how="left")

    return base


# ---------------------------------------------------------------------------
# Orquestrador
# ---------------------------------------------------------------------------
def transformar_gold(silver_dfs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """
    Orquestrador da camada Gold. Recebe as tabelas Silver e retorna
    um dicionário com todas as tabelas Gold prontas para carga.
    """
    log.info("[GOLD] Iniciando transformação da camada Gold.")

    tabelas_esperadas = {"entradas", "doacoes", "prontuarios", "saidas"}
    for tabela in tabelas_esperadas:
        if tabela not in silver_dfs:
            raise ValueError(f"[GOLD] Tabela Silver '{tabela}' não encontrada. Abortando.")

    gold: dict[str, pd.DataFrame] = {}

    # 1. Gerar OBTs
    log.info("[GOLD] Gerando gold_entradas...")
    gold["gold_entradas"] = gerar_gold_entradas(silver_dfs["entradas"])

    log.info("[GOLD] Gerando gold_doacoes...")
    gold["gold_doacoes"] = gerar_gold_doacoes(silver_dfs["doacoes"])

    log.info("[GOLD] Gerando gold_prontuarios...")
    gold["gold_prontuarios"] = gerar_gold_prontuarios(silver_dfs["prontuarios"])

    log.info("[GOLD] Gerando gold_saidas...")
    gold["gold_saidas"] = gerar_gold_saidas(silver_dfs["saidas"])

    # 2. Gerar dimensão calendário mensal
    log.info("[GOLD] Gerando dim_calendario_mensal...")
    datas = []
    for df in silver_dfs.values():
        for col in df.columns:
            if col.startswith("data_"):
                datas.append(pd.to_datetime(df[col].dropna()))
    if not datas:
        raise ValueError("[GOLD] Nenhuma data disponível para gerar dim_calendario.")
    todas_datas = pd.concat(datas)
    dim_mensal = gerar_dim_calendario_mensal(todas_datas.min(), todas_datas.max())
    gold["dim_calendario_mensal"] = dim_mensal

    # 3. Gerar saldo mensal de animais
    log.info("[GOLD] Gerando gold_animais_mensal...")
    gold["gold_animais_mensal"] = gerar_gold_animais_mensal(
        silver_dfs["entradas"], silver_dfs["saidas"], dim_mensal
    )

    log.info("[GOLD] Transformação Gold concluída com sucesso.")
    return gold