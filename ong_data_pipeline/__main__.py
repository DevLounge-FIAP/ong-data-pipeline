from .extract import extrair_dados_bronze
from .transform import transformar_dados
from .config import get_engine
from .load import carregar_para_dw


def main():
    bronze = extrair_dados_bronze()
    silver = transformar_dados(bronze)

    engine = get_engine()
    carregar_para_dw(silver, engine=engine)


if __name__ == "__main__":
    main()
