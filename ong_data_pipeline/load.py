import logging
from typing import Optional
import pandas as pd

log = logging.getLogger(__name__)


def carregar_para_dw(silver: dict[str, pd.DataFrame], engine: Optional[object] = None, if_exists: str = "replace"):
    """Carrega os DataFrames silver para o datawarehouse MySQL via SQLAlchemy engine.

    Se `engine` for None, a função faz um dry-run e apenas loga as tabelas.
    """
    if engine is None:
        log.info("Nenhum engine de banco configurado — executando dry-run. As tabelas abaixo seriam carregadas:")
        for nome, df in silver.items():
            log.info(f" - {nome}: {len(df)} linhas, {len(df.columns)} colunas")
        return

    for nome, df in silver.items():
        tabela = f"silver_{nome}"
        if df is None or df.empty:
            log.info(f"Pular carregamento: tabela {tabela} vazia")
            continue

        log.info(f"Carregando {tabela} ({len(df)} linhas) → DW")
        # pandas.to_sql usa a conexão do engine via SQLAlchemy
        try:
            df.to_sql(tabela, con=engine, if_exists=if_exists, index=False)
        except Exception as e:
            log.error(f"Erro ao carregar tabela {tabela}: {e}")
            raise
