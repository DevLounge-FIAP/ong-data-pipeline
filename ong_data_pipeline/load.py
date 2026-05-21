import logging
from typing import Optional
import pandas as pd

log = logging.getLogger(__name__)


def carregar_para_dw(silver: dict[str, pd.DataFrame], engine: Optional[object] = None, if_exists: str = "replace"):
    """Em desenvolvimento
    """

    for nome, df in silver.items():
        tabela = f"silver_{nome}"
        if df is None or df.empty:
            log.info(f"Pular carregamento: tabela {tabela} vazia")
            continue

        log.info(f"Carregando {tabela} ({len(df)} linhas) → DW")

