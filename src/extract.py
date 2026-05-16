import os
import gspread
import pandas as pd
from dotenv import load_dotenv

# Carrega as senhas e chaves do arquivo .env (que não vai para o GitHub)
load_dotenv()

def extrair_dados_bronze():
    """
    Conecta no Google Sheets e extrai as abas brutas para DataFrames.
    Retorna um dicionário com os DataFrames da Camada Bronze.
    """
    print("Iniciando extração da Camada Bronze...")
    
    # Busca as variáveis seguras do arquivo .env
    caminho_credenciais = os.getenv("GOOGLE_CREDENTIALS_PATH")
    id_planilha = os.getenv("GOOGLE_SHEET_ID")
    
    # Validar que as variáveis de ambiente estão configuradas
    if not caminho_credenciais:
        raise ValueError("Variável de ambiente GOOGLE_CREDENTIALS_PATH não configurada. Verifique o arquivo .env")
    if not id_planilha:
        raise ValueError("Variável de ambiente GOOGLE_SHEET_ID não configurada. Verifique o arquivo .env")
    
    # Autenticação
    client = gspread.service_account(filename=caminho_credenciais)
    
    # Abrir a planilha
    planilha = client.open_by_key(id_planilha)
    
    # Extrair as abas para DataFrames
    df_doacoes = pd.DataFrame(planilha.worksheet("Controle de Doações").get_all_records())
    df_saidas = pd.DataFrame(planilha.worksheet("Registro de Adoção / Saída").get_all_records()) 
    df_prontuario = pd.DataFrame(planilha.worksheet("Prontuário Médico e Rotina").get_all_records())
    df_entradas = pd.DataFrame(planilha.worksheet("Entrada / Novo Resgate").get_all_records())
    
    print("Extração concluída com sucesso!")
    
    # Retorna tudo junto
    return {
        "doacoes": df_doacoes,
        "saidas": df_saidas,
        "prontuarios": df_prontuario,
        "entradas": df_entradas
    }

# Bloco de teste local 
if __name__ == "__main__":
    dados_brutos = extrair_dados_bronze()
    print("\nVisualizando as primeiras linhas da aba de Entradas:")
    print(dados_brutos["entradas"].head())
    print("\nVisualizando as primeiras linhas da aba de Prontuarios:")
    print(dados_brutos["prontuarios"].head())
    print("\nVisualizando as primeiras linhas da aba de Saidas:")
    print(dados_brutos["saidas"].head())
    print("\nVisualizando as primeiras linhas da aba de Doações:")
    print(dados_brutos["doacoes"].head())