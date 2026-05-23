import os
import json
import logging
import time
import gspread
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# Nome exato das abas na planilha centralizado aqui para facilitar manutenção
#Guarda as abas dentro de um dicionario.
ABAS = {
    "doacoes":     "Controle de Doações",
    "saidas":      "Registro de Adoção / Saída",
    "prontuarios": "Prontuário Médico e Rotina",
    "entradas":    "Entrada / Novo Resgate",
}

#Autenticação do Google Spread Sheet
def _autenticar() -> gspread.Client:

    '''ARGS:
        Função retorna gspread.service_account, ou seja a autenticação
    '''
    credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")  #Basicamente procura a credencial do google no env para não ficar exposta

    if credentials_json:
        log.info("Autenticando via GOOGLE_CREDENTIALS_JSON (GitHub Actions)")
        try:
            info = json.loads(credentials_json)
        except json.JSONDecodeError as e:
            raise ValueError(
                "GOOGLE_CREDENTIALS_JSON contém JSON inválido."
            ) from e
        return gspread.service_account_from_dict(info)

    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
    if credentials_path:
        log.info(f"Autenticando via arquivo: {credentials_path}")
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Arquivo de credenciais não encontrado: {credentials_path}"
            )
        return gspread.service_account(filename=credentials_path)

    raise ValueError(
        "Nenhuma credencial do Google configurada."
    )


def _is_retryable_api_error(error: gspread.exceptions.APIError) -> bool:
    response = getattr(error, "response", None)
    status_code = getattr(response, "status_code", None)
    return status_code in RETRYABLE_STATUS_CODES


def _executar_com_retentativas(descricao: str, operacao, max_tentativas: int = 4, base_delay: float = 1.0):
    for tentativa in range(1, max_tentativas + 1):
        try:
            return operacao()
        except gspread.exceptions.APIError as error:
            if tentativa >= max_tentativas or not _is_retryable_api_error(error):
                raise

            response = getattr(error, "response", None)
            status_code = getattr(response, "status_code", "desconhecido")
            delay = base_delay * (2 ** (tentativa - 1))
            log.warning(
                f"{descricao} falhou com status {status_code}; "
                f"retentativa {tentativa}/{max_tentativas} em {delay:.1f}s"
            )
            time.sleep(delay)


def _ler_aba(planilha: gspread.Spreadsheet, chave: str) -> pd.DataFrame:
    nome_aba = ABAS[chave]
    try:
        aba = _executar_com_retentativas(
            f"Abertura da aba '{nome_aba}'",
            lambda: planilha.worksheet(nome_aba),
        )
    except gspread.exceptions.WorksheetNotFound:
        raise ValueError(f"Aba '{nome_aba}' não encontrada na planilha.")

    valores = _executar_com_retentativas(
        f"Leitura da aba '{nome_aba}'",
        lambda: aba.get_all_values(),
    )

    if not valores or len(valores) < 2:
        log.warning(f"Aba '{nome_aba}' está vazia ou só tem cabeçalho — retornando DataFrame vazio")
        cabecalho = valores[0] if valores else []
        return pd.DataFrame(columns=cabecalho)

    cabecalho, *linhas = valores
    df = pd.DataFrame(linhas, columns=cabecalho)

    log.info(f"  '{nome_aba}': {len(df)} linhas x {len(df.columns)} colunas extraídas")
    return df


def extrair_dados_bronze() -> dict[str, pd.DataFrame]:
    log.info("Iniciando extração da Camada Bronze...")

    id_planilha = os.getenv("GOOGLE_SHEET_ID")
    if not id_planilha:
        raise ValueError("Variável de ambiente GOOGLE_SHEET_ID não configurada.")

    client = _autenticar()

    try:
        planilha = client.open_by_key(id_planilha) #Abre por chave da planilha
    except gspread.exceptions.SpreadsheetNotFound:
        raise ValueError(f"Planilha com ID '{id_planilha}' não encontrada.")

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
