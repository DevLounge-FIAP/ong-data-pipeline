import logging
import pandas as pd
from pandas_gbq import to_gbq

log = logging.getLogger(__name__)

BIGQUERY_SCHEMAS: dict[str, list[dict[str, str]]] = {
    "silver_entradas": [
        {"name": "carimbo_ts", "type": "TIMESTAMP", "mode": "REQUIRED"},
        {"name": "data_entrada", "type": "DATE", "mode": "REQUIRED"},
        {"name": "email_responsavel", "type": "STRING", "mode": "NULLABLE"},
        {"name": "nome_responsavel", "type": "STRING", "mode": "NULLABLE"},
        {"name": "sobrenome_responsavel", "type": "STRING", "mode": "NULLABLE"},
        {"name": "especie", "type": "STRING", "mode": "NULLABLE"},
        {"name": "sexo", "type": "STRING", "mode": "NULLABLE"},
        {"name": "porte", "type": "STRING", "mode": "NULLABLE"},
        {"name": "condicao_saude", "type": "STRING", "mode": "NULLABLE"},
        {"name": "historico", "type": "STRING", "mode": "NULLABLE"},
        {"name": "nome_completo", "type": "STRING", "mode": "NULLABLE"},
        {"name": "flag_multiplas_condicoes", "type": "INTEGER", "mode": "NULLABLE"},
    ],
    "silver_doacoes": [
        {"name": "carimbo_ts", "type": "TIMESTAMP", "mode": "REQUIRED"},
        {"name": "data_doacao", "type": "DATE", "mode": "REQUIRED"},
        {"name": "email_doador", "type": "STRING", "mode": "NULLABLE"},
        {"name": "tipo_doacao", "type": "STRING", "mode": "NULLABLE"},
        {"name": "tipo_doador", "type": "STRING", "mode": "NULLABLE"},
        {"name": "valor_doado", "type": "FLOAT", "mode": "NULLABLE"},
        {"name": "categoria_medicamento", "type": "STRING", "mode": "NULLABLE"},
        {"name": "nome_medicamento", "type": "STRING", "mode": "NULLABLE"},
        {"name": "nome_doador", "type": "STRING", "mode": "NULLABLE"},
    ],
    "silver_prontuarios": [
        {"name": "carimbo_ts", "type": "TIMESTAMP", "mode": "REQUIRED"},
        {"name": "data_procedimento", "type": "DATE", "mode": "REQUIRED"},
        {"name": "email_profissional", "type": "STRING", "mode": "NULLABLE"},
        {"name": "nome_profissional", "type": "STRING", "mode": "NULLABLE"},
        {"name": "tipo_evento", "type": "STRING", "mode": "NULLABLE"},
        {"name": "categoria_medicamento", "type": "STRING", "mode": "NULLABLE"},
        {"name": "nome_medicamento", "type": "STRING", "mode": "NULLABLE"},
        {"name": "categoria_vacina", "type": "STRING", "mode": "NULLABLE"},
        {"name": "nome_vacina", "type": "STRING", "mode": "NULLABLE"},
        {"name": "nome_cirurgia", "type": "STRING", "mode": "NULLABLE"},
    ],
    "silver_saidas": [
        {"name": "carimbo_ts", "type": "TIMESTAMP", "mode": "REQUIRED"},
        {"name": "data_saida", "type": "DATE", "mode": "REQUIRED"},
        {"name": "nome_animal", "type": "STRING", "mode": "NULLABLE"},
        {"name": "motivo_saida", "type": "STRING", "mode": "NULLABLE"},
        {"name": "nome_adotante", "type": "STRING", "mode": "NULLABLE"},
        {"name": "telefone", "type": "STRING", "mode": "NULLABLE"},
        {"name": "cidade_destino", "type": "STRING", "mode": "NULLABLE"},
        {"name": "bairro_destino", "type": "STRING", "mode": "NULLABLE"},
        {"name": "num_imovel", "type": "STRING", "mode": "NULLABLE"},
        {"name": "tipo_imovel", "type": "STRING", "mode": "NULLABLE"},
    ],
}


def _schema_bigquery(tabela: str) -> list[dict[str, str]]:
    try:
        return BIGQUERY_SCHEMAS[tabela]
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
        

