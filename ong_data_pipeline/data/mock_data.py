import random
import uuid
from datetime import datetime, timedelta
import pandas as pd
from faker import Faker

fake = Faker("pt_BR")

NUM_ANIMAIS = 500

def gerar_dados_ong():
# ------------------------------------------------------------
# 1. GERAR TABELA: Entrada
# ------------------------------------------------------------
    lista_animais = []
    nomes_pets = [
            "Thor",
            "Mel",
            "Luna",
            "Belinha",
            "Bob",
            "Amora",
            "Rex",
            "Marley",
            "Fred",
            "Nina",
            "Pipoca",
            "Pretinha",
            "Caramelo",
            "Cacau",
            "Toby",
            "Luke",
            "Maia",
            "Max",
            "Zeus",
            "Bidu",
        ]
    nome_do_responsavel = [
            "Aelton",
            "Michelly",
            "Victor",
            "Bruno"
        ]
    sobrenome_do_responsavel = [
        "Soares",
        "Santos",
        "Mantovani",
        ]
    especie_do_animal = [
        "Cão",
        "Gato",
        "Bovino",
        "Equino",
        "Suíno",
        "Ovino/Caprino",
        "Ave",
        "Peixe",
        "Animal silvestres",
        "Pet exótico"
        ]
    sexo = [
        "Macho",
        "Fêmea",
        "Desconhecido"
    ]
    for _ in range(NUM_ANIMAIS):
        id_animal = str(uuid.uuid4())[:8]
        # 1. Gerar Data de Entrada base
        data_de_entrada = fake.date_between(start_date="-1y", end_date="today")
        
        # 2. Gerar carimbo_ts (Data de Entrada + Horário Aleatório formatado com barras)
        horario_aleatorio = timedelta(
            hours=random.randint(7, 19), 
            minutes=random.randint(0, 59), 
            seconds=random.randint(0, 59)
        )
        datetime_completo = datetime.combine(data_de_entrada, datetime.min.time()) + horario_aleatorio
        carimbo_ts_formatado = datetime_completo.strftime("%d/%m/%Y %H:%M:%S")
        
        # 3. Gerar e-mail dinâmico baseado no responsável do sorteio
        nome_resp = random.choice(nome_do_responsavel)
        sobrenome_resp = random.choice(sobrenome_do_responsavel)
        endereco_email = f"{nome_resp.lower()}.{sobrenome_resp.lower()}@ongamigos.org"
        
        # 4. Gerar condicao_de_saude tratando a lógica de EnumList (múltiplas escolhas separadas por vírgula)
        estrutura_saude = random.choice(["Saudável", "Desconhecido", "Comorbidades"])
        if estrutura_saude == "Comorbidades":
            # Sorteia de 1 a 2 problemas de saúde para simular a marcação múltipla do AppSheet
            problemas_sorteados = random.sample(["Ferido", "Doente", "Desnutrido"], k=random.randint(1, 2))
            condicao_de_saude = ", ".join(problemas_sorteados)
        else:
            condicao_de_saude = estrutura_saude
        lista_animais.append(
            {
                "id_animal": id_animal,
                "carimbo_ts": carimbo_ts_formatado,
                "endereco_email": endereco_email,
                "data_de_entrada": data_de_entrada,
                "nome_do_responsavel": nome_resp,
                "sobrenome_do_responsavel": sobrenome_resp,
                "nome_animal": random.choice(nomes_pets),
                "especie_do_animal": random.choice(especie_do_animal),
                "sexo": random.choice(sexo),
                "porte": random.choice(["Médio", "Pequeno", "Grande"]),
                "condicao_de_saude": condicao_de_saude,
                "status_atual": "No Abrigo"
            }
        )
    df_entradas = pd.DataFrame(lista_animais)
# ------------------------------------------------------------
# 2. GERAR TABELA: Prontuário Médico e Rotina
# ------------------------------------------------------------
    lista_prontuarios = []
    tipos_de_evento = [
        "Medicamento",
        "Vacina",
        "Consulta Veterinária", # Corrigido erro de digitação
        "Cirurgia",
        "Castração"
    ]
    
    # Preenchimento das listas vazias com dados fictícios para não quebrar o random.choice()
    medicamentos = {
        "Antibiótico": ["Amoxicilina", "Doxiciclina", "Enrofloxacina"],
        "Anti-inflamatórios / Analgésico": ["Meloxicam", "Carprofeno", "Prednisolona"],
        "Antiparasitário interno": ["Simparic", "Bravecto", "Ivermectina"],
        "Antiparasitario externo": ["Frontline", "NexGard", "Bravecto Top"],
        "Antifúngico": ["Cetoconazol", "Itraconazol"],
        "Antiviral": ["Interferon", "Aciclovir"],
        "Antialérgico": ["Apoquel", "Loratadina"],
        "Gastrointestinal": ["Omeprazol", "Ondansetrona", "Sucralfato"],
        "Cardiológico": ["Pimobendan", "Enalapril"],
        "Respiratório": ["Acetilcisteína", "Aminofilina"],
        "Dermatológico": ["Pomada Cicatrizante", "Shampoo Clorexidina"],
        "Oftálmico": ["Colírio Tobramicina", "Pomada Oftálmica"],
        "Ontológico": ["Limpador Auricular", "Gota Otológica"],
        "Hormônio": ["Levotiroxina", "Insulina"],
        "Anestésico / Sedativo": ["Propofol", "Acepromazina", "Cetamina"],
        "Suplementos / Vitaminas": ["Vitamina B12", "Ômega 3", "Cálcio"],
        "Outro": ["Soro Fisiológico", "Glicose"]
    }
    
    vacinas = {
        "Antirrábica": ["Vacina Antirrábica Padrão"],
        "Polivalente": ["V8", "V10", "V4 Felina", "V5 Felina"],
        "Respiratória": ["Vacina Gripe Canina (Bordetella)"],
        "Gastrointestinal": ["Vacina Giárdia"],
        "Reprodutiva": ["Vacina Específica"],
        "Leptospirose": ["Vacina Leptospirose (Isolada)"],
        "Cinomose": ["Vacina Cinomose (Isolada)"],
        "Parvovirose": ["Vacina Parvovirose (Isolada)"],
        "Panleucopenia": ["Vacina Panleucopenia"],
        "Calicivirose": ["Vacina Calicivirose"],
        "Rinotraqueíte": ["Vacina Rinotraqueíte"],
        "Clostridial": ["Polivalente Clostridial"],
        "Brucelose": ["Vacina Brucelose"],
        "Marek": ["Vacina Doença de Marek"],
        "Newcastle": ["Vacina Newcastle"],
        "Influenza": ["Vacina Influenza Equina/Aviária"],
        "Tétano": ["Soro Antitetânico", "Toxoide Tetânico"],
    }

    # Gera de 1 a 4 prontuários para a maioria dos animais
    for index, animal in df_entradas.iterrows():
        num_procedimentos = random.randint(1, 4)
        for _ in range(num_procedimentos):
            id_procedimento = str(uuid.uuid4())[:8]
            tipo_ev = random.choice(tipos_de_evento)

            # Garante que o prontuário aconteceu DEPOIS da entrada do animal
            data_prontuario = fake.date_between_dates(
                date_start=animal["data_de_entrada"], date_end=datetime.today()
            )
            
            horario_aleatorio = timedelta(
                hours=random.randint(8, 18), 
                minutes=random.randint(0, 59), 
                seconds=random.randint(0, 59)
            )
            carimbo_ts = datetime.combine(data_prontuario, datetime.min.time()) + horario_aleatorio

            # Inicializa campos condicionais como vazios
            cat_med, nome_med, cat_vac, nome_vac, nome_cirurgia = "", "", "", "", ""
            
            # Aplica as regras de negócio dinâmicas do AppSheet (Show_If)
            if tipo_ev == "Medicamento":
                cat_med = random.choice(list(medicamentos.keys()))
                nome_med = random.choice(medicamentos[cat_med])
            elif tipo_ev == "Vacina":
                cat_vac = random.choice(list(vacinas.keys()))
                nome_vac = random.choice(vacinas[cat_vac])
            elif tipo_ev == "Cirurgia":
                nome_cirurgia = random.choice(
                    ["Ortopedia", "Castração Emergencial", "Remoção de Nódulo", "Amputação"]
                )
            elif tipo_ev == "Castração":
                nome_cirurgia = "Castração Eletiva"

            lista_prontuarios.append(
                {
                    "id_procedimento": id_procedimento,
                    "id_animal": animal["id_animal"],
                    "carimbo_ts": carimbo_ts.strftime("%d/%m/%Y %H:%M:%S"), # Padrão Sheets com barras
                    "data_do_procedimento": data_prontuario.strftime("%d/%m/%Y"), # Apenas a data
                    "nome_do_profissional": animal["nome_do_responsavel"], # Herda o nome gerado na tabela de entrada
                    "tipo_de_evento": tipo_ev,
                    "categoria_medicamento": cat_med,
                    "nome_medicamento": nome_med,
                    "categoria_vacina": cat_vac,
                    "nome_vacina": nome_vac,
                    "nome_cirurgia_realizada": nome_cirurgia,
                }
            )
            
    df_prontuarios = pd.DataFrame(lista_prontuarios)
# ------------------------------------------------------------
# 3. GERAR TABELA: Saidas
# ------------------------------------------------------------
    lista_saidas = []
    tipo_do_imovel = ["Casa","Sobrado","Apartamento","Kitnet"]

    animais_que_sairam = df_entradas.sample(frac=0.4) #Seleciona 40% dos animais para terem saida

    for index, animal in animais_que_sairam.iterrows():
        id_saida = str(uuid.uuid4())[:8]
        motivo_da_saida = random.choice(["Adoção Definitiva","Lar Temporário","Óbito","Fuga","Transferência"])

        # Atualiza o status do animal na tabela mãe (Entradas) para refletir a saída
        df_entradas.loc[df_entradas["id_animal"] == animal["id_animal"], "status_atual"] = motivo_da_saida

        #Garantir que a saida só ocorra após a entrada
        data_da_saida = fake.date_between_dates(
            date_start=animal["data_de_entrada"], date_end=datetime.today()
        )

        # Gerar o carimbo de tempo específico para a saída
        horario_aleatorio = timedelta(
            hours=random.randint(8, 18), 
            minutes=random.randint(0, 59), 
            seconds=random.randint(0, 59)
        )
        carimbo_ts_saida = datetime.combine(data_da_saida, datetime.min.time()) + horario_aleatorio

        if motivo_da_saida not in ["Óbito", "Fuga"]:
            nome_adotante = fake.name()
            telefone = fake.cellphone_number()
            cidade_de_destino = "Passo Fundo"
            bairro_de_destino = fake.bairro()
            numero_do_imovel = fake.building_number()
            tipo_imovel = random.choice(tipo_do_imovel)
        else:
            nome_adotante = ""
            telefone = ""
            cidade_de_destino = ""
            bairro_de_destino = ""
            numero_do_imovel = ""
            tipo_imovel = ""

        lista_saidas.append(
                {
                    "id_saida": id_saida,
                    "id_animal": animal["id_animal"],
                    "carimbo_ts": carimbo_ts_saida.strftime("%d/%m/%Y %H:%M:%S"),
                    "data_da_saida": data_da_saida.strftime("%d/%m/%Y"),
                    "motivo_da_saida": motivo_da_saida,
                    "nome_do_adotante_tutor": nome_adotante,
                    "telefone_de_contato": telefone,
                    "cidade_de_destino": cidade_de_destino,
                    "bairro_de_destino": bairro_de_destino,
                    "numero_do_imovel":numero_do_imovel,
                    "tipo_do_imovel": tipo_imovel
                    
                }
            )
    
    df_saidas = pd.DataFrame(lista_saidas)

    # Convertendo datas das entradas para string antes de exportar
    df_entradas["data_de_entrada"] = df_entradas["data_de_entrada"].apply(
        lambda x: x.strftime("%d-%m-%Y")
    )

    df_entradas.to_csv("mock_entradas.csv", index=False, encoding="utf-8-sig")
    df_prontuarios.to_csv("mock_protuarios.csv", index=False, encoding="utf-8-sig")
    df_saidas.to_csv("mock_saidas.csv", index=False, encoding="utf-8-sig")

    print(f"{len(df_entradas)} Animais cadastrados.")
    print(f"{len(df_prontuarios)} Atendimentos médicos gerados.")
    print(f"{len(df_saidas)} Saidas geradas")

if __name__ == "__main__":
    gerar_dados_ong()