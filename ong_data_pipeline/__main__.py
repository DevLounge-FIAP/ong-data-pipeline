"""
Pipeline ONG Data Pipeline – Medalhão (Bronze → Silver → Gold)

Fluxo:
  1. Extrai dados brutos da planilha (Bronze)          ← extract.py
  2. Transforma e valida → Silver                      ← transform/silver.py
  3. Carrega Silver no BigQuery                        ← load/bigquery.py
  4. Gera métricas → Gold (a partir da Silver em memória) ← transform/gold.py
  5. Carrega Gold no BigQuery                          ← load/bigquery.py

Fail‑fast: qualquer exceção interrompe o processo, sem cargas parciais.
"""

import os
import logging
import sys

from .core.config import get_bq_config
from .extract.extract import extrair_dados_bronze
from .transform.silver import transformar_dados as transformar_silver
from .transform.gold import transformar_gold
from .load.bigquery import carregar_silver_para_dw, carregar_gold_para_dw

# ---------------------------------------------------------------------------
# Configuração básica de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("ong.pipeline")

# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------
def main():
    log.info("=== INÍCIO DO PIPELINE ===")

    try:
        # 1. Configurações do BigQuery
        project_id, dataset_id = get_bq_config()

        # 2. Extração (Bronze) – extract.py cuida da autenticação e leitura da planilha
        log.info("Extraindo dados da planilha...")
        dados_bronze = extrair_dados_bronze()
        log.info(f"Extração concluída: {len(dados_bronze)} abas obtidas.")

        # 3. Transformação Silver
        log.info("Iniciando transformação Silver...")
        silver = transformar_silver(dados_bronze)
        log.info(f"Silver gerada com {len(silver)} tabelas.")

        # 4. Carga Silver
        log.info("Carregando Silver no BigQuery...")
        carregar_silver_para_dw(silver, project_id, dataset_id)
        log.info("Carga Silver concluída com sucesso.")

        # 5. Transformação Gold (usa os DataFrames Silver em memória)
        log.info("Iniciando transformação Gold...")
        gold = transformar_gold(silver)
        log.info(f"Gold gerada com {len(gold)} tabelas.")

        # 6. Carga Gold
        log.info("Carregando Gold no BigQuery...")
        carregar_gold_para_dw(gold, project_id, dataset_id)
        log.info("Carga Gold concluída com sucesso.")

        log.info("=== PIPELINE FINALIZADO COM SUCESSO ===")

    except Exception as erro:
        log.error(f"Falha crítica: {erro}", exc_info=True)
        log.error("Pipeline abortado devido a erro.")
        sys.exit(1)

# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()