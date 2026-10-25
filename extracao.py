import requests

def buscar_veiculo (tipos):
  url = f'https://parallelum.com.br/fipe/api/v1/{tipos}/marcas'
  response = requests.get(url)
  dados = response.json()

  return dados