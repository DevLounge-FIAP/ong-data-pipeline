def schemas_silver():
    """
    Esquemas da Camada Silver.
    Refletem exatamente as colunas e os tipos de dados gerados após
    a limpeza do silver.py, alinhados com o novo front-end no AppSheet.
    """
    BIGQUERY_SCHEMAS_SILVER: dict[str, list[dict[str, str]]] = {
        "silver_entradas": [
            {"name": "id_animal", "type": "STRING", "mode": "REQUIRED"},
            {"name": "carimbo_ts", "type": "TIMESTAMP", "mode": "REQUIRED"},
            {"name": "data_entrada", "type": "DATE", "mode": "REQUIRED"},
            {"name": "nome_responsavel", "type": "STRING", "mode": "NULLABLE"},
            {"name": "sobrenome_responsavel", "type": "STRING", "mode": "NULLABLE"},
            {"name": "nome_completo", "type": "STRING", "mode": "NULLABLE"},
            {"name": "especie", "type": "STRING", "mode": "NULLABLE"},
            {"name": "sexo", "type": "STRING", "mode": "NULLABLE"},
            {"name": "porte", "type": "STRING", "mode": "NULLABLE"},
            {"name": "condicao_saude", "type": "STRING", "mode": "NULLABLE"},
            {"name": "historico", "type": "STRING", "mode": "NULLABLE"},
            {"name": "status_atual", "type": "STRING", "mode": "NULLABLE"},
            {"name": "flag_multiplas_condicoes", "type": "BOOL", "mode": "NULLABLE"},
            {"name": "is_saudavel", "type": "BOOL", "mode": "NULLABLE"},
            {"name": "is_ferido", "type": "BOOL", "mode": "NULLABLE"},
            {"name": "is_doente", "type": "BOOL", "mode": "NULLABLE"},
            {"name": "is_desnutrido", "type": "BOOL", "mode": "NULLABLE"},
        ],
        "silver_doacoes": [
            {"name": "id_doacao", "type": "STRING", "mode": "REQUIRED"},
            {"name": "carimbo_ts", "type": "TIMESTAMP", "mode": "REQUIRED"},
            {"name": "data_doacao", "type": "DATE", "mode": "REQUIRED"},
            {"name": "tipo_doacao", "type": "STRING", "mode": "NULLABLE"},
            {"name": "tipo_doador", "type": "STRING", "mode": "NULLABLE"},
            {"name": "nome_doador", "type": "STRING", "mode": "NULLABLE"},
            {"name": "valor_doado", "type": "FLOAT", "mode": "NULLABLE"},
            {"name": "categoria_medicamento", "type": "STRING", "mode": "NULLABLE"},
            {"name": "nome_medicamento", "type": "STRING", "mode": "NULLABLE"},
            {"name": "comprovante_foto", "type": "STRING", "mode": "NULLABLE"},
        ],
        "silver_prontuarios": [
            {"name": "id_procedimento", "type": "STRING", "mode": "REQUIRED"},
            {"name": "id_animal", "type": "STRING", "mode": "REQUIRED"},
            {"name": "carimbo_ts", "type": "TIMESTAMP", "mode": "REQUIRED"},
            {"name": "data_procedimento", "type": "DATE", "mode": "REQUIRED"},
            {"name": "nome_profissional", "type": "STRING", "mode": "NULLABLE"},
            {"name": "tipo_evento", "type": "STRING", "mode": "NULLABLE"},
            {"name": "categoria_medicamento", "type": "STRING", "mode": "NULLABLE"},
            {"name": "nome_medicamento", "type": "STRING", "mode": "NULLABLE"},
            {"name": "categoria_vacina", "type": "STRING", "mode": "NULLABLE"},
            {"name": "nome_vacina", "type": "STRING", "mode": "NULLABLE"},
            {"name": "nome_cirurgia", "type": "STRING", "mode": "NULLABLE"},
            {"name": "observacoes_medicas", "type": "STRING", "mode": "NULLABLE"},
        ],
        "silver_saidas": [
            {"name": "id_saida", "type": "STRING", "mode": "REQUIRED"},
            {"name": "id_animal", "type": "STRING", "mode": "REQUIRED"},
            {"name": "carimbo_ts", "type": "TIMESTAMP", "mode": "REQUIRED"},
            {"name": "data_saida", "type": "DATE", "mode": "REQUIRED"},
            {"name": "motivo_saida", "type": "STRING", "mode": "NULLABLE"},
            {"name": "nome_adotante", "type": "STRING", "mode": "NULLABLE"},
            {"name": "telefone_adotante", "type": "STRING", "mode": "NULLABLE"},
            {"name": "cidade_destino", "type": "STRING", "mode": "NULLABLE"},
            {"name": "bairro_destino", "type": "STRING", "mode": "NULLABLE"},
            {"name": "num_imovel", "type": "INTEGER", "mode": "NULLABLE"},
            {"name": "tipo_imovel", "type": "STRING", "mode": "NULLABLE"},
            {"name": "observacoes", "type": "STRING", "mode": "NULLABLE"},
        ],
    }
    return BIGQUERY_SCHEMAS_SILVER


def schemas_gold():
    """
    Esquemas da Camada Gold.
    Refletem as OBTs (One Big Tables) prontas para consumo direto
    no Looker Studio, já com as dimensões cruzadas.
    """
    BIGQUERY_SCHEMAS_GOLD: dict[str, list[dict[str, str]]] = {
        "gold_entradas": [
            {"name": "ano", "type": "INTEGER", "mode": "REQUIRED"},
            {"name": "mes", "type": "INTEGER", "mode": "REQUIRED"},
            {"name": "ano_mes", "type": "STRING", "mode": "REQUIRED"},
            {"name": "especie", "type": "STRING", "mode": "NULLABLE"},
            {"name": "sexo", "type": "STRING", "mode": "NULLABLE"},
            {"name": "porte", "type": "STRING", "mode": "NULLABLE"},
            {"name": "condicao_saude", "type": "STRING", "mode": "NULLABLE"},
            {"name": "total_entradas", "type": "INTEGER", "mode": "REQUIRED"},
        ],
        "gold_doacoes": [
            {"name": "ano", "type": "INTEGER", "mode": "REQUIRED"},
            {"name": "mes", "type": "INTEGER", "mode": "REQUIRED"},
            {"name": "ano_mes", "type": "STRING", "mode": "REQUIRED"},
            {"name": "tipo_doacao", "type": "STRING", "mode": "NULLABLE"},
            {"name": "tipo_doador", "type": "STRING", "mode": "NULLABLE"},
            {"name": "total_doacoes", "type": "INTEGER", "mode": "REQUIRED"},
            {"name": "soma_valor_doado", "type": "FLOAT", "mode": "NULLABLE"},
            {"name": "media_valor_doado", "type": "FLOAT", "mode": "NULLABLE"},
            {"name": "maior_doacao", "type": "FLOAT", "mode": "NULLABLE"},
            {"name": "menor_doacao", "type": "FLOAT", "mode": "NULLABLE"},
        ],
        "gold_prontuarios": [
            {"name": "ano", "type": "INTEGER", "mode": "REQUIRED"},
            {"name": "mes", "type": "INTEGER", "mode": "REQUIRED"},
            {"name": "ano_mes", "type": "STRING", "mode": "REQUIRED"},
            {"name": "tipo_evento", "type": "STRING", "mode": "NULLABLE"},
            {"name": "nome_profissional", "type": "STRING", "mode": "NULLABLE"},
            {"name": "especie", "type": "STRING", "mode": "NULLABLE"},
            {"name": "sexo", "type": "STRING", "mode": "NULLABLE"},
            {"name": "porte", "type": "STRING", "mode": "NULLABLE"},
            {"name": "total_procedimentos", "type": "INTEGER", "mode": "REQUIRED"},
        ],
        "gold_saidas": [
            {"name": "ano", "type": "INTEGER", "mode": "REQUIRED"},
            {"name": "mes", "type": "INTEGER", "mode": "REQUIRED"},
            {"name": "ano_mes", "type": "STRING", "mode": "REQUIRED"},
            {"name": "motivo_saida", "type": "STRING", "mode": "NULLABLE"},
            {"name": "cidade_destino", "type": "STRING", "mode": "NULLABLE"},
            {"name": "bairro_destino", "type": "STRING", "mode": "NULLABLE"},
            {"name": "especie", "type": "STRING", "mode": "NULLABLE"},
            {"name": "sexo", "type": "STRING", "mode": "NULLABLE"},
            {"name": "porte", "type": "STRING", "mode": "NULLABLE"},
            {"name": "total_saidas", "type": "INTEGER", "mode": "REQUIRED"},
        ],
        "dim_calendario_mensal": [
            {"name": "data", "type": "DATE", "mode": "REQUIRED"},
            {"name": "ano", "type": "INTEGER", "mode": "REQUIRED"},
            {"name": "mes", "type": "INTEGER", "mode": "REQUIRED"},
            {"name": "ano_mes", "type": "STRING", "mode": "REQUIRED"},
            {"name": "nome_mes", "type": "STRING", "mode": "NULLABLE"},
            {"name": "trimestre", "type": "INTEGER", "mode": "NULLABLE"},
            {"name": "ano_mes_num", "type": "INTEGER", "mode": "REQUIRED"},
        ],
        "gold_animais_mensal": [
            {"name": "ano_mes", "type": "STRING", "mode": "REQUIRED"},
            {"name": "total_entradas", "type": "INTEGER", "mode": "REQUIRED"},
            {"name": "total_saidas", "type": "INTEGER", "mode": "REQUIRED"},
            {"name": "saldo_liquido", "type": "INTEGER", "mode": "REQUIRED"},
            {"name": "saldo_acumulado", "type": "INTEGER", "mode": "REQUIRED"},
            {"name": "ano", "type": "INTEGER", "mode": "REQUIRED"},
            {"name": "mes", "type": "INTEGER", "mode": "REQUIRED"},
            {"name": "nome_mes", "type": "STRING", "mode": "NULLABLE"},
            {"name": "trimestre", "type": "INTEGER", "mode": "NULLABLE"},
        ],
    }
    return BIGQUERY_SCHEMAS_GOLD