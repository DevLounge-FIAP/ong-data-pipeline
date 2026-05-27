def schemas_silver():
    BIGQUERY_SCHEMAS_SILVER: dict[str, list[dict[str, str]]] = {
        "silver_entradas": [
            {"name": "carimbo_ts", "type": "TIMESTAMP", "mode": "REQUIRED"},
            {"name": "data_entrada", "type": "DATE", "mode": "REQUIRED"},
            {"name": "email_responsavel", "type": "STRING", "mode": "NULLABLE"},
            {"name": "nome_responsavel", "type": "STRING", "mode": "NULLABLE"},
            {"name": "sobrenome_responsavel", "type": "STRING", "mode": "NULLABLE"},
            {"name": "especie", "type": "STRING", "mode": "NULLABLE"},
            {"name": "sexo", "type": "STRING", "mode": "NULLABLE"},
            {"name": "porte", "type": "STRING", "mode": "NULLABLE"},
            {"name": "condicao_saude", "type": "STRING", "mode": "NULLABLE"},
            {"name": "historico", "type": "STRING", "mode": "NULLABLE"},
            {"name": "nome_completo", "type": "STRING", "mode": "NULLABLE"},
            {"name": "flag_multiplas_condicoes", "type": "INTEGER", "mode": "NULLABLE"},
            {"name": "is_doente", "type": "BOOL", "mode": "NULLABLE"},
            {"name": "is_saudavel", "type": "BOOL", "mode": "NULLABLE"},
            {"name": "is_ferido", "type": "BOOL", "mode": "NULLABLE"},
            {"name": "is_desconhecido", "type": "BOOL", "mode": "NULLABLE"},
            {"name": "is_desnutrido", "type": "BOOL", "mode": "NULLABLE"},
            {"name": "id_animal", "type": "STRING", "mode": "REQUIRED"},
        ],
        "silver_doacoes": [
            {"name": "carimbo_ts", "type": "TIMESTAMP", "mode": "REQUIRED"},
            {"name": "data_doacao", "type": "DATE", "mode": "REQUIRED"},
            {"name": "email_doador", "type": "STRING", "mode": "NULLABLE"},
            {"name": "tipo_doacao", "type": "STRING", "mode": "NULLABLE"},
            {"name": "tipo_doador", "type": "STRING", "mode": "NULLABLE"},
            {"name": "valor_doado", "type": "FLOAT", "mode": "NULLABLE"},
            {"name": "categoria_medicamento", "type": "STRING", "mode": "NULLABLE"},
            {"name": "nome_medicamento", "type": "STRING", "mode": "NULLABLE"},
            {"name": "nome_doador", "type": "STRING", "mode": "NULLABLE"},
        ],
        "silver_prontuarios": [
            {"name": "carimbo_ts", "type": "TIMESTAMP", "mode": "REQUIRED"},
            {"name": "data_procedimento", "type": "DATE", "mode": "REQUIRED"},
            {"name": "email_profissional", "type": "STRING", "mode": "NULLABLE"},
            {"name": "nome_profissional", "type": "STRING", "mode": "NULLABLE"},
            {"name": "tipo_evento", "type": "STRING", "mode": "NULLABLE"},
            {"name": "categoria_medicamento", "type": "STRING", "mode": "NULLABLE"},
            {"name": "nome_medicamento", "type": "STRING", "mode": "NULLABLE"},
            {"name": "categoria_vacina", "type": "STRING", "mode": "NULLABLE"},
            {"name": "nome_vacina", "type": "STRING", "mode": "NULLABLE"},
            {"name": "nome_cirurgia", "type": "STRING", "mode": "NULLABLE"},
        ],
        "silver_saidas": [
            {"name": "carimbo_ts", "type": "TIMESTAMP", "mode": "REQUIRED"},
            {"name": "data_saida", "type": "DATE", "mode": "REQUIRED"},
            {"name": "nome_animal", "type": "STRING", "mode": "NULLABLE"},
            {"name": "motivo_saida", "type": "STRING", "mode": "NULLABLE"},
            {"name": "nome_adotante", "type": "STRING", "mode": "NULLABLE"},
            {"name": "telefone", "type": "STRING", "mode": "NULLABLE"},
            {"name": "cidade_destino", "type": "STRING", "mode": "NULLABLE"},
            {"name": "bairro_destino", "type": "STRING", "mode": "NULLABLE"},
            {"name": "num_imovel", "type": "STRING", "mode": "NULLABLE"},
            {"name": "tipo_imovel", "type": "STRING", "mode": "NULLABLE"},
        ],
    }
    return BIGQUERY_SCHEMAS_SILVER

def schemas_gold():
    BIGQUERY_SCHEMAS_GOLD: dict[str, list[dict[str, str]]] = {
        
    }
    return BIGQUERY_SCHEMAS_GOLD