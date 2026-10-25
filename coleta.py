import os
import requests
from banco import criar_tabela, inserir_veiculos
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN_API") 
headers = {"Authorization": f"Bearer {TOKEN}"}

criar_tabela()

tipos_veiculos = ['carros', 'motos', 'caminhoes']

total = 0

for tipo in tipos_veiculos:
    url = f'https://parallelum.com.br/fipe/api/v1/{tipo}/marcas'
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        marcas = response.json()
        for marca in marcas:
            inserir_veiculos(
                0.0,                        
                marca.get('nome', ''),      
                '',                         
                0,                          
                '',                         
                marca.get('codigo', ''),    
                tipo                        
            )
            total += 1
    else:
        print(f'Erro {response.status_code} em {url}')
        print(response.text)

print(f'{total} registros inseridos')