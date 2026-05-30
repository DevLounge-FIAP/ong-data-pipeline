import os
import logging
import gspread
import pandas as pd
from ..core.config import obter_planilha_autenticada, ler_aba_com_retentativas

log = logging.getLogger(__name__)

# Nome exato das abas na planilha centralizado aqui para facilitar manutenção
# Guarda as abas dentro de um dicionário.
# É o contrato do projeto
ABAS = {
    "doacoes":     "Controle de Doações",
    "saidas":      "Registro de Adoção / Saída",
    "prontuarios": "Prontuário Médico e Rotina",
    "entradas":    "Entrada / Novo Resgate",
}


def _ler_aba(planilha: gspread.Spreadsheet, chave: str) -> pd.DataFrame:
    nome_aba = ABAS[chave]
    valores = ler_aba_com_retentativas(planilha, nome_aba)

    if not valores or len(valores) < 2:
        log.warning(f"Aba '{nome_aba}' está vazia ou só tem cabeçalho — retornando DataFrame vazio")
        cabecalho = valores[0] if valores else []
        return pd.DataFrame(columns=cabecalho)

    cabecalho, *linhas = valores
    df = pd.DataFrame(linhas, columns=cabecalho)

    log.info(f"  '{nome_aba}': {len(df)} linhas x {len(df.columns)} colunas extraídas")
    return df


def extrair_dados_bronze() -> dict[str, pd.DataFrame]:
    """
    Retorna um dicionário de DataFrames para cada aba da planilha.
    """
    log.info("Iniciando extração da Camada Bronze...")

    # Agora usa GOOGLE_SHEETS_ID (plural) para padronizar com o restante do projeto
    id_planilha = os.getenv("GOOGLE_SHEETS_ID")
    if not id_planilha:
        raise ValueError("Variável de ambiente GOOGLE_SHEETS_ID não configurada.")

    planilha = obter_planilha_autenticada(id_planilha)

    dados = {}
    falhas = []

    for chave in ABAS:
        try:
            dados[chave] = _ler_aba(planilha, chave)
        except ValueError as e:
            log.error(f"Falha ao extrair aba '{ABAS[chave]}': {e}")
            falhas.append(chave)

    if falhas:
        abas_falhas = [ABAS[k] for k in falhas]
        raise RuntimeError(f"Extração concluída com erros nas abas: {abas_falhas}")

    log.info(f"Extração concluída — {len(dados)} abas extraídas com sucesso.")
    return dados


if __name__ == "__main__":
    dados_brutos = extrair_dados_bronze()
    for chave, df in dados_brutos.items():
        print(f"\n{'='*50}")
        print(f"Aba: {ABAS[chave]}  ({len(df)} linhas)")
        print(df.head(3).to_string())