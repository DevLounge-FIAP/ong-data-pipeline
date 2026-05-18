import logging

from .extract import extrair_dados_bronze
from .transform import transformar_dados
from .config import get_engine
from .load import carregar_para_dw

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)


def main():
    log.info("Iniciando pipeline ETL")

    bronze = extrair_dados_bronze()
    silver = transformar_dados(bronze)

    engine = get_engine()
    carregar_para_dw(silver, engine=engine)

    log.info("Pipeline concluído")


if __name__ == "__main__":
    main()
