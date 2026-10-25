import os
import requests
from banco import criar_tabela, inserir_veiculos

TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOiJjM2FkYzc2OC1jNzNhLTRhOTAtOWE1Mi0xMGMyMzYxYzU4NjYiLCJlbWFpbCI6ImZyYW5jaXNjb2RldjIzOThAZ21haWwuY29tIiwianRpIjoiODE4OWYwZjUtNmVmOS00ZjM5LWE0ZjktMjVmMmRlMWJkY2Y2IiwiaWF0IjoxNzkyODk3MjA4fQ.5tSTWmqErEyTKVd_b6xR6Y_JSupMh5Sz1hK4I6togK4"
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