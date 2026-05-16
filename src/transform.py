import pandas as pd
df = pd.read_excel(r"PipelineV2.xlsx", sheet_name="Registro de Adoção  Saída")

#Apenas colunas que vou utilizar
colunas_selecionadas = [
    "Nome do Animal",
    "  Motivo da Saída  ",
    "Nome do Adotante/Tutor  ",
    "Telefone do Adotante/Tutor ",
    "Cidade de Destino",
    "Bairro de Destino  ",
    "Tipo do Imovél"
]

df = df[colunas_selecionadas]

#renomear colunas para codar melhor
df = df.rename(columns={
     "Nome do Animal"               : "nome_animal",
    "  Motivo da Saída  "          : "motivo_saida",
    "Nome do Adotante/Tutor  "     : "nome_adotante",
    "Telefone do Adotante/Tutor "  : "telefone",
    "Cidade de Destino"            : "cidade_destino",
    "Bairro de Destino  "          : "bairro_destino",
    "Tipo do Imovél"               : "tipo_imovel"
})

#limpar espaços das colunas
colunas_texto = ["nome_animal", "motivo_saida", "nome_adotante",
                 "cidade_destino", "bairro_destino", "tipo_imovel"]

for coluna in colunas_texto:
    df[coluna] = df[coluna].str.strip()

#definir telefones como uma string 
df['telefone'] = df['telefone'].astype(str)

#colocar sempre a primeira letra do imovel maiuscula e o resto minuscula
df['tipo_imovel'] = df["tipo_imovel"].str.title()

#Finalizando
print(f'Total de registros: {len(df)}')
print(df.to_string(index=False))

print("\nDistribuição por motivo de saída:")
print(df['motivo_saida'].value_counts())
