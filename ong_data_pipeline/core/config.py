import os
from dotenv import load_dotenv

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
