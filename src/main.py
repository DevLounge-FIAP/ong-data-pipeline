from extract import extrair_dados_bronze
from transform import transformar_dados

bronze = extrair_dados_bronze()
silver = transformar_dados(bronze)