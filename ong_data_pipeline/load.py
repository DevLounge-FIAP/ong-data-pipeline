import logging
import pandas as pd
from pandas_gbq import to_gbq

log = logging.getLogger(__name__)

def carregar_para_dw(silver: dict[str, pd.DataFrame], project_id: str, dataset_id: str) -> None:
    """Carrega os DataFrames da camada Silver para o BigQuery."""
    if not project_id or not dataset_id:
        raise ValueError("project_id e dataset_id são obrigatórios para carregar no BigQuery.")

    for nome, df in silver.items():
        tabela = f"silver_{nome}"
        if df is None or df.empty:
            log.info(f"Pular carregamento: tabela {tabela} vazia")
            continue

        log.info(f"Carregando {tabela} ({len(df)} linhas) → DW")

        destino = f"{dataset_id}.{tabela}"

        try:
            to_gbq(
                dataframe=df,
                destination_table=destino,
                project_id=project_id,
                if_exists="append",
            )
            log.info(f"Sucesso: {destino} atualizada no BigQuery!")
        except Exception as e:
            log.error(f"Erro ao carregar tabela {destino}: {e}")
            raise


        