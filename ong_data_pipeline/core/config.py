import os
from dotenv import load_dotenv
import logging
import gspread
import json
import time

load_dotenv()

def get_bq_config() -> tuple[str, str]:
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID")
    
    missing = [
        nome
        for nome, valor in (
            ("GCP_PROJECT_ID", project_id),
            ("BQ_DATASET_ID", dataset_id),
        )
        if not valor
    ]
    if missing:
        raise ValueError(
            "Variáveis de ambiente ausentes para BigQuery: " + ", ".join(missing)
        )

    assert project_id is not None
    assert dataset_id is not None

    return project_id, dataset_id

log = logging.getLogger(__name__)
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


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