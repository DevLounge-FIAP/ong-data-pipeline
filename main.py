import argparse
import logging

from .extract.extract import extrair_dados_bronze
from .transform.silver import transformar_dados
from .load.bigquery import carregar_para_dw
from .core.config import get_bq_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

#Função para visualar os df no terminal --Só teste
def _preview(bronze: dict, silver: dict, rows: int = 5) -> None:
    log.info(f"Preview das primeiras {rows} linhas por aba — Bronze")
    for nome, df in bronze.items():
        print("\n" + "=" * 60)
        print(f"BRONZE — {nome} ({len(df)} linhas, {len(df.columns)} colunas)")
        try:
            print(df.head(rows).to_string(index=False))
        except Exception:
            print(df.head(rows))

    log.info(f"Preview das primeiras {rows} linhas por aba — Silver")
    for nome, df in silver.items():
        print("\n" + "=" * 60)
        print(f"SILVER — {nome} ({len(df)} linhas, {len(df.columns)} colunas)")
        try:
            print(df.head(rows).to_string(index=False))
        except Exception:
            print(df.head(rows))


def main(argv: list | None = None) -> None:
    parser = argparse.ArgumentParser(description="Runner do pipeline ONG Data Pipeline")
    parser.add_argument("--preview", action="store_true",
                        help="Mostra as primeiras linhas de cada aba (bronze/silver) no terminal")
    parser.add_argument("--rows", type=int, default=5,
                        help="Número de linhas a mostrar em --preview (padrão: 5)")
    args = parser.parse_args(argv)

    log.info("Iniciando pipeline ETL")

    bronze = extrair_dados_bronze()
    silver = transformar_dados(bronze)

    if args.preview:
        _preview(bronze, silver, rows=args.rows)
        log.info("Preview concluído")
        return


    project_id, dataset_id = get_bq_config()
    carregar_para_dw(silver, project_id, dataset_id)
    
    log.info("Pipeline concluído")


if __name__ == "__main__":
    main()
