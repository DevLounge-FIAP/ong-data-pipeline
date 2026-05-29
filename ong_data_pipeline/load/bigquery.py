import logging
import pandas as pd
from pandas_gbq import to_gbq
from .schemas import schemas_silver

log = logging.getLogger(__name__)

def _schema_bigquery(tabela: str) -> list[dict[str, str]]:
    try:
        return schemas_silver()[tabela]
    except KeyError as error:
        raise ValueError(f"Nenhum schema BigQuery definido para '{tabela}'.") from error


def _validar_dataframe_para_schema(tabela: str, df: pd.DataFrame) -> None:
    schema = _schema_bigquery(tabela)
    colunas_esperadas = [campo["name"] for campo in schema]
    colunas_df = list(df.columns)

    faltantes = [coluna for coluna in colunas_esperadas if coluna not in df.columns]
    extras = [coluna for coluna in colunas_df if coluna not in colunas_esperadas]
    if faltantes or extras:
        raise ValueError(
            f"Colunas incompatíveis para {tabela}. "
            f"Faltantes: {faltantes or '[]'}; extras: {extras or '[]'}"
        )

    for campo in schema:
        nome = campo["name"]
        tipo = campo["type"]
        if tipo in {"DATE", "TIMESTAMP"} and not pd.api.types.is_datetime64_any_dtype(df[nome]):
            raise TypeError(
                f"Coluna '{nome}' em {tabela} precisa ser datetime64 para BigQuery ({tipo})."
            )

def carregar_para_dw(silver: dict[str, pd.DataFrame], project_id: str, dataset_id: str) -> None:
    """Carrega os DataFrames da camada Silver para o BigQuery usando full refresh."""
    if not project_id or not dataset_id:
        raise ValueError("project_id e dataset_id são obrigatórios para carregar no BigQuery.")

    for nome, df in silver.items():
        tabela = f"silver_{nome}"
        if df is None or df.empty:
            log.info(f"Pular carregamento: tabela {tabela} vazia")
            continue

        _validar_dataframe_para_schema(tabela, df)

        log.info(f"Carregando {tabela} ({len(df)} linhas) → DW")

        destino = f"{dataset_id}.{tabela}"

        try:
            to_gbq(
                dataframe=df,
                destination_table=destino,
                project_id=project_id,
                if_exists="replace",
                table_schema=_schema_bigquery(tabela),
            )
            log.info(f"Sucesso: {destino} recarregada no BigQuery!")
        except Exception as e:
            log.error(f"Erro ao carregar tabela {destino}: {e}")
            raise
        

