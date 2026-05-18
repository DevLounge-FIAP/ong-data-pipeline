(The file `c:\Dev\Projetos\ong-data-pipeline\README.md` exists, but is empty)
ONG Data Pipeline
=================

Resumo
------
Pipeline ETL que extrai 4 abas de um Google Sheet (alimentado por Google Forms), aplica transformações (arquitetura medalhão: Bronze → Silver → Gold) e carrega para um MySQL (Aiven) para consumo no Looker.

Requisitos
---------
- Python 3.10 ou superior

Quickstart (local)
-------------------
1. Crie um arquivo `.env` com as variáveis necessárias:

	- `GOOGLE_SHEET_ID` — ID da planilha
	- `GOOGLE_CREDENTIALS_PATH` ou `GOOGLE_CREDENTIALS_JSON` — credenciais da service account
	- `AIVEN_DB_URL` ou `SQLALCHEMY_DATABASE_URL` — string de conexão para o MySQL

2. Instale dependências:

```bash
pip install -r requirements.txt
```

3. Execute o pipeline (dry-run se `AIVEN_DB_URL` não estiver configurado):

```bash
python -m ong_data_pipeline
```

CI / GitHub Actions
--------------------
Configure os secrets no repositório:

- `GOOGLE_CREDENTIALS_JSON` — conteúdo do JSON da service account (recomendado para Actions)
- `GOOGLE_SHEET_ID`
- `AIVEN_DB_URL`

O workflow está em `.github/workflows/etl.yml` e roda manualmente ou por cron.
