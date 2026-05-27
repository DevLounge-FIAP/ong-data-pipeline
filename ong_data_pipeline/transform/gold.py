import logging
import pandas as pd

log = logging.getLogger(__name__)

def gerar_fato_movimentacao(df_entradas: pd.DataFrame, df_saidas: pd.DataFrame) -> pd.DataFrame:
    """
    Une as entradas e saídas para calcular o tempo médio de permanência dos elementos na ONG.
    Assume que 'nome_completo' e 'especie' servem como chave composta de identificação.
    """
    log.info("[GOLD] A gerar Fato de Movimentação (Entradas vs Saídas)...")
    
    # Validação defensiva básica
    if df_entradas.empty:
        log.warning("O DataFrame de entradas está vazio. Fato de movimentação será vazio.")
        return pd.DataFrame()

    # Faz o cruzamento (Left Join: mantém todos os que entraram, independentemente de terem saído)
    df_fato = pd.merge(
        df_entradas,
        df_saidas,
        on=["nome_completo", "especie"],  # Ajuste estas chaves conforme o seu schema real
        how="left",
        suffixes=("_entrada", "_saida")
    )

    # Verifica se as colunas de data existem antes de calcular a diferença
    if "data_entrada" in df_fato.columns and "data_saida" in df_fato.columns:
        # Garante a tipagem de datetime
        df_fato["data_entrada"] = pd.to_datetime(df_fato["data_entrada"])
        df_fato["data_saida"] = pd.to_datetime(df_fato["data_saida"])
        
        # Calcula os dias de permanência (resultará em NaN para os que ainda não saíram)
        df_fato["tempo_permanencia_dias"] = (df_fato["data_saida"] - df_fato["data_entrada"]).dt.days

    return df_fato


def gerar_dim_saude_mensal(df_prontuarios: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa os prontuários por mês e condição de saúde para análise de volume de atendimentos.
    """
    log.info("[GOLD] A gerar Dimensão de Saúde Mensal...")
    
    if df_prontuarios.empty or "data_atendimento" not in df_prontuarios.columns:
        return pd.DataFrame()

    # Cria uma cópia para evitar o aviso "SettingWithCopyWarning" do Pandas
    df = df_prontuarios.copy()
    
    # Trunca a data para o primeiro dia do mês (ex: 2025-05-15 -> 2025-05-01)
    df["data_atendimento"] = pd.to_datetime(df["data_atendimento"])
    df["mes_ano"] = df["data_atendimento"].dt.to_period("M").dt.to_timestamp()

    # Define as colunas de agrupamento (assumindo que existe uma coluna 'condicao_saude' ou similar)
    colunas_agrupamento = ["mes_ano"]
    if "condicao_saude" in df.columns:
        colunas_agrupamento.append("condicao_saude")

    # Realiza a agregação (contagem de atendimentos)
    df_dim = df.groupby(colunas_agrupamento).size().reset_index(name="total_atendimentos")
    
    return df_dim


def gerar_fato_financeiro(df_doacoes: pd.DataFrame) -> pd.DataFrame:
    """
    Consolida as doações monetárias e físicas por período (mês).
    """
    log.info("[GOLD] A gerar Fato Financeiro...")
    
    if df_doacoes.empty or "data_doacao" not in df_doacoes.columns:
        return pd.DataFrame()

    df = df_doacoes.copy()
    df["data_doacao"] = pd.to_datetime(df["data_doacao"])
    df["mes_ano"] = df["data_doacao"].dt.to_period("M").dt.to_timestamp()

    # Exemplo de agregação múltipla: soma de valores e contagem de doadores
    agregacoes = {}
    if "valor" in df.columns:
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
        agregacoes["valor"] = "sum"
        
    agregacoes["data_doacao"] = "count"  # Conta o número total de transações/doações

    df_fato = df.groupby("mes_ano").agg(agregacoes).rename(columns={"data_doacao": "qtd_doacoes"}).reset_index()

    return df_fato


def transformar_dados_gold(silver: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """
    Wrapper orquestrador da camada Gold.
    Recebe o dicionário Silver validado e devolve os DataFrames agregados.
    """
    log.info("[GOLD] A iniciar a transformação da camada de negócio (Business Layer)")
    gold: dict[str, pd.DataFrame] = {}

    # 1. Fato de Movimentação
    if "entradas" in silver and "saidas" in silver:
        gold["fato_movimentacao"] = gerar_fato_movimentacao(silver["entradas"], silver["saidas"])

    # 2. Dimensão Saúde Mensal
    if "prontuarios" in silver:
        gold["dim_saude_mensal"] = gerar_dim_saude_mensal(silver["prontuarios"])

    # 3. Fato Financeiro
    if "doacoes" in silver:
        gold["fato_financeiro"] = gerar_fato_financeiro(silver["doacoes"])

    return gold