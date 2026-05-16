import os
import json
import logging
import gspread
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# Nome exato das abas na planilha centralizado aqui para facilitar manutenção
ABAS = {
    "doacoes":     "Controle de Doações",
    "saidas":      "Registro de Adoção / Saída",
    "prontuarios": "Prontuário Médico e Rotina",
    "entradas":    "Entrada / Novo Resgate",
}


# ---------------------------------------------------------------------------
# AUTENTICAÇÃO
# Suporta dois modos sem bifurcação manual:
#   - Local:           GOOGLE_CREDENTIALS_PATH aponta para o arquivo .json
#   - GitHub Actions:  GOOGLE_CREDENTIALS_JSON contém o conteúdo do .json
# ---------------------------------------------------------------------------

def _autenticar() -> gspread.Client:
    """
    Tenta autenticar via conteúdo JSON (Actions) e,
    se não encontrar, cai para o caminho do arquivo (local).
    """
    credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")

    if credentials_json:
        log.info("Autenticando via GOOGLE_CREDENTIALS_JSON (GitHub Actions)")
        try:
            info = json.loads(credentials_json)
        except json.JSONDecodeError as e:
            raise ValueError(
                "GOOGLE_CREDENTIALS_JSON contém JSON inválido. "
                "Verifique o secret no GitHub Actions."
            ) from e
        return gspread.service_account_from_dict(info)

    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
    if credentials_path:
        log.info(f"Autenticando via arquivo: {credentials_path}")
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Arquivo de credenciais não encontrado: {credentials_path}\n"
                "Verifique se o caminho no .env está correto e se o arquivo "
                "existe fora do repositório."
            )
        return gspread.service_account(filename=credentials_path)

    raise ValueError(
        "Nenhuma credencial do Google configurada.\n"
        "Configure uma das variáveis no .env:\n"
        "  GOOGLE_CREDENTIALS_PATH  → caminho para o .json (uso local)\n"
        "  GOOGLE_CREDENTIALS_JSON  → conteúdo do .json  (GitHub Actions)"
    )


# ---------------------------------------------------------------------------
# LEITURA DE ABA
# ---------------------------------------------------------------------------

def _ler_aba(planilha: gspread.Spreadsheet, chave: str) -> pd.DataFrame:
    """
    Lê uma aba pelo nome definido em ABAS[chave].
    Retorna DataFrame com todas as colunas do cabeçalho,
    mesmo quando há células vazias.
    """
    nome_aba = ABAS[chave]
    try:
        aba = planilha.worksheet(nome_aba)
    except gspread.exceptions.WorksheetNotFound:
        raise ValueError(
            f"Aba '{nome_aba}' não encontrada na planilha.\n"
            "Verifique se o nome está exatamente igual ao do Google Sheets "
            "(espaços, acentos e maiúsculas importam)."
        )

    valores = aba.get_all_values()

    if not valores or len(valores) < 2:
        log.warning(f"Aba '{nome_aba}' está vazia ou só tem cabeçalho — retornando DataFrame vazio")
        cabecalho = valores[0] if valores else []
        return pd.DataFrame(columns=cabecalho)

    cabecalho, *linhas = valores
    df = pd.DataFrame(linhas, columns=cabecalho)

    log.info(f"  '{nome_aba}': {len(df)} linhas x {len(df.columns)} colunas extraídas")
    return df


# ---------------------------------------------------------------------------
# EXTRAÇÃO PRINCIPAL
# ---------------------------------------------------------------------------

def extrair_dados_bronze() -> dict[str, pd.DataFrame]:
    """
    Conecta no Google Sheets e extrai todas as abas como DataFrames brutos.
    Cada aba é lida de forma independente.

    Retorna dicionário com os DataFrames da Camada Bronze.
    As chaves são: 'doacoes', 'saidas', 'prontuarios', 'entradas'.
    """
    log.info("Iniciando extração da Camada Bronze...")

    id_planilha = os.getenv("GOOGLE_SHEET_ID")
    if not id_planilha:
        raise ValueError(
            "Variável de ambiente GOOGLE_SHEET_ID não configurada. "
            "Verifique o arquivo .env"
        )

    client = _autenticar()

    try:
        planilha = client.open_by_key(id_planilha)
    except gspread.exceptions.SpreadsheetNotFound:
        raise ValueError(
            f"Planilha com ID '{id_planilha}' não encontrada.\n"
            "Verifique se o GOOGLE_SHEET_ID no .env está correto e se a "
            "service account tem permissão de leitura na planilha."
        )

    dados = {}
    falhas = []

    for chave in ABAS:
        try:
            dados[chave] = _ler_aba(planilha, chave)
        except Exception as e:
            log.error(f"Falha ao extrair aba '{ABAS[chave]}': {e}")
            falhas.append(chave)

    if falhas:
        abas_falhas = [ABAS[k] for k in falhas]
        raise RuntimeError(
            f"Extração concluída com erros nas abas: {abas_falhas}\n"
            "Corrija os erros acima antes de prosseguir para o transform."
        )

    log.info(f"Extração concluída — {len(dados)} abas extraídas com sucesso.")
    return dados


# ---------------------------------------------------------------------------
# TESTE LOCAL
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    dados_brutos = extrair_dados_bronze()

    for chave, df in dados_brutos.items():
        print(f"\n{'='*50}")
        print(f"Aba: {ABAS[chave]}  ({len(df)} linhas)")
        print(df.head(3).to_string())