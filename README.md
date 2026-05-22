ONG Data Pipeline
=================

Resumo
------
Pipeline ETL que extrai 4 abas de um Google Sheet (alimentado por Google Forms), aplica transformações na camada Silver e carrega os dados no BigQuery para consumo analítico atraves do Looker.

O carregamento no BigQuery usa full refresh por tabela (`replace`) e o acesso ao Google Sheets possui retentativas para erros transitórios como `429`.

Requisitos
---------
- Python 3.10 ou superior

Quickstart (local)
-------------------
1. Crie um arquivo `.env` com as variáveis necessárias:

	- `GOOGLE_SHEET_ID` — ID da planilha
	- `GOOGLE_CREDENTIALS_PATH` ou `GOOGLE_CREDENTIALS_JSON` — credenciais da service account
	- `GCP_PROJECT_ID` — projeto do BigQuery
	- `BQ_DATASET_ID` — dataset de destino no BigQuery

2. Instale dependências:

```bash
pip install -r requirements.txt
```

3. Execute o pipeline:

```bash
python -m ong_data_pipeline
```

Use `--preview` para validar extração e transformação sem carregar no BigQuery.

CI / GitHub Actions
--------------------
Configure os secrets no repositório:

- `GOOGLE_CREDENTIALS_JSON` — conteúdo do JSON da service account (recomendado para Actions)
- `GOOGLE_SHEET_ID`
- `GCP_PROJECT_ID`
- `BQ_DATASET_ID`

O workflow está em `.github/workflows/etl.yml` e roda manualmente ou por cron.
