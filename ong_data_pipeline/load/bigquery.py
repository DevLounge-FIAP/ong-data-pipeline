import logging
import pandas as pd
from pandas_gbq import to_gbq
from .schemas import schemas_silver, schemas_gold

log = logging.getLogger(__name__)


def _obter_schema(tabela: str, schema_func) -> list[dict[str, str]]:
    try:
        return schema_func()[tabela]
    except KeyError as error:
        raise ValueError(f"Nenhum schema definido para '{tabela}'.") from error


def _validar_dataframe_para_schema(
    tabela: str, df: pd.DataFrame, schema_func
) -> None:
    schema = _obter_schema(tabela, schema_func)
    colunas_esperadas = [campo["name"] for campo in schema]
    colunas_df = list(df.columns)

    faltantes = [col for col in colunas_esperadas if col not in df.columns]
    extras = [col for col in colunas_df if col not in colunas_esperadas]
    if faltantes or extras:
        raise ValueError(
            f"Colunas incompatíveis para {tabela}. "
            f"Faltantes: {faltantes or '[]'}; extras: {extras or '[]'}"
        )

    for campo in schema:
        nome = campo["name"]
        tipo = campo["type"]
        if tipo == "DATE" and not pd.api.types.is_datetime64_any_dtype(df[nome]):
            raise TypeError(
                f"Coluna '{nome}' em {tabela} precisa ser datetime64 (DATE)."
            )
        if tipo == "TIMESTAMP":
            if not pd.api.types.is_datetime64_any_dtype(df[nome]):
                raise TypeError(
                    f"Coluna '{nome}' em {tabela} precisa ser datetime64 (TIMESTAMP)."
                )
            # Opcional: exigir UTC para evitar ambiguidades
            if df[nome].dt.tz is None:
                log.warning(
                    f"Coluna '{nome}' em {tabela} não tem fuso horário; "
                    "o BigQuery assumirá UTC. Considere usar tz_localize('UTC') na Silver."
                )


def carregar_tabelas(
    tabelas: dict[str, pd.DataFrame],
    schema_func,
    project_id: str,
    dataset_id: str,
    prefixo: str = "",
) -> None:
    """
    Carrega um dicionário de DataFrames no BigQuery com full refresh.

    Args:
        tabelas: Dicionário {nome_base: DataFrame}.
        schema_func: Função que retorna os schemas (ex.: schemas_silver).
        project_id, dataset_id: Identificadores do GCP.
        prefixo: Prefixo adicionado ao nome da tabela no BQ.
    """
    if not project_id or not dataset_id:
        raise ValueError("project_id e dataset_id são obrigatórios.")

    for nome, df in tabelas.items():
        if df is None:
            raise ValueError(
                f"DataFrame para '{nome}' é None. A carga foi abortada."
            )

        tabela = f"{prefixo}{nome}" if prefixo else nome
        _validar_dataframe_para_schema(tabela, df, schema_func)

        destino = f"{dataset_id}.{tabela}"
        log.info(f"Carregando {tabela} ({len(df)} linhas) → {destino}")

        try:
            to_gbq(
                dataframe=df,
                destination_table=destino,
                project_id=project_id,
                if_exists="replace",
                table_schema=_obter_schema(tabela, schema_func),
            )
            log.info(f"Sucesso: {destino} atualizada no BigQuery!")
        except Exception as e:
            log.error(f"Erro ao carregar tabela {destino}: {e}")
            raise

    log.info(
        f"Carga concluída: {len(tabelas)} tabela(s) processada(s)."
    )


# Wrappers específicos para manter compatibilidade com o orquestrador
def carregar_silver_para_dw(
    silver: dict[str, pd.DataFrame], project_id: str, dataset_id: str
) -> None:
    carregar_tabelas(silver, schemas_silver, project_id, dataset_id, prefixo="silver_")


def carregar_gold_para_dw(
    gold: dict[str, pd.DataFrame], project_id: str, dataset_id: str
) -> None:
    carregar_tabelas(gold, schemas_gold, project_id, dataset_id, prefixo="")