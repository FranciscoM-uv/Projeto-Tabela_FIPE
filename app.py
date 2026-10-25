import sqlite3
import requests
import streamlit as st
import pandas as pd
from banco import criar_tabela_historico, inserir_historico
import os
from dotenv import load_dotenv

criar_tabela_historico()

st.set_page_config(page_title="Consulta Tabela FIPE", page_icon="🚗", layout='wide')

st.title("🚗 Consulta Tabela FIPE")

load_dotenv()

TOKEN_API = os.getenv("TOKEN_API")

HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'X-Subscription-Token': TOKEN_API
}

def buscar_tipos():
    conexao = sqlite3.connect("fipe.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT DISTINCT tipo_veiculo FROM veiculos")
    tipos = [row[0] for row in cursor.fetchall()]
    conexao.close()
    return tipos

def buscar_marcas(tipo):
    conexao = sqlite3.connect("fipe.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT DISTINCT marcas, codigo_fipe FROM veiculos WHERE tipo_veiculo = ? ORDER BY marcas", (tipo,))
    marcas = cursor.fetchall()
    conexao.close()
    return marcas

tipos_disponiveis = buscar_tipos()

if tipos_disponiveis:
    tipo_veiculo = st.selectbox("1. Selecione o Tipo de Veículo:", tipos_disponiveis)

    marcas_db = buscar_marcas(tipo_veiculo)
    
    if marcas_db:
        opcoes_marcas = {nome: codigo for nome, codigo in marcas_db}
        marca_sel = st.selectbox("2. Selecione a Marca:", list(opcoes_marcas.keys()))
        cod_marca = opcoes_marcas[marca_sel]

        url_modelos = f"https://parallelum.com.br/fipe/api/v1/{tipo_veiculo}/marcas/{cod_marca}/modelos"
        res_modelos = requests.get(url_modelos, headers=HEADERS)

        if res_modelos.status_code == 200:
            dados_modelos = res_modelos.json().get('modelos', [])
            opcoes_modelos = {m['nome']: m['codigo'] for m in dados_modelos}
            
            if opcoes_modelos:
                modelo_sel = st.selectbox("3. Selecione o Modelo:", list(opcoes_modelos.keys()))
                cod_modelo = opcoes_modelos[modelo_sel]

                url_anos = f"https://parallelum.com.br/fipe/api/v1/{tipo_veiculo}/marcas/{cod_marca}/modelos/{cod_modelo}/anos"
                res_anos = requests.get(url_anos, headers=HEADERS)

                if res_anos.status_code == 200:
                    anos_dados = res_anos.json()
                    opcoes_anos = {a['nome']: a['codigo'] for a in anos_dados}
                    
                    if opcoes_anos:
                        ano_sel = st.selectbox("4. Selecione o Ano:", list(opcoes_anos.keys()))
                        cod_ano = opcoes_anos[ano_sel]

                        if st.button("Consultar Preço", type="primary"):
                            url_preco = f"https://parallelum.com.br/fipe/api/v1/{tipo_veiculo}/marcas/{cod_marca}/modelos/{cod_modelo}/anos/{cod_ano}"
                            res_preco = requests.get(url_preco, headers=HEADERS)
                            
                            if res_preco.status_code == 200:
                                dados = res_preco.json()
                                st.success("Consulta efetuada com sucesso!")
                                st.subheader(f"💰 Preço: {dados.get('Valor')}")
                                st.write(f"**Marca:** {dados.get('Marca')}")
                                st.write(f"**Modelo:** {dados.get('Modelo')}")
                                st.write(f"**Ano/Modelo:** {dados.get('AnoModelo')}")
                                st.write(f"**Combustível:** {dados.get('Combustivel')}")
                                st.write(f"**Código FIPE:** {dados.get('CodigoFipe')}")
                                st.write(f"**Mês Referência:** {dados.get('MesReferencia')}")
                            else:
                                st.error(f"Erro ao buscar preço (Código {res_preco.status_code})")
                    else:
                        st.warning("Nenhum ano disponível para este modelo.")
                else:
                    st.error(f"Erro ao buscar anos (Código {res_anos.status_code})")
            else:
                st.warning("Nenhum modelo encontrado para esta marca.")
        else:
            st.error(f"Erro ao comunicar com a API (Código {res_modelos.status_code}): {res_modelos.text}")
    else:
        st.warning("Nenhuma marca encontrada no banco de dados.")
else:
    st.info("A base de dados está vazia ou o tipo de veículo não foi encontrado.")
    
if st.button("Consultar Histórico de preços", type="primary", key="btn_consultar_preco"):
    url_preco = f"https://parallelum.com.br/fipe/api/v1/{tipo_veiculo}/marcas/{cod_marca}/modelos/{cod_modelo}/anos/{cod_ano}"
    res_preco = requests.get(url_preco, headers=HEADERS)
    
    if res_preco.status_code == 200:
        dados = res_preco.json()
        
        valor_str = dados.get('Valor').replace('R$ ', '').replace('.', '').replace(',', '.')
        preco_atual_num = float(valor_str)
        
        inserir_historico(
            marca=dados.get('Marca'),
            modelo=dados.get('Modelo'),
            ano=dados.get('AnoModelo'),
            preco=preco_atual_num,
            mes_referencia=dados.get('MesReferencia')
        )
        
        st.success("Consulta efetuada e salva no histórico!")
        
        conexao = sqlite3.connect("fipe.db")
        query = """
            SELECT modelo as produto, preco, mes_referencia 
            FROM historico_consultas 
            WHERE marca = ? AND modelo = ? AND ano = ?
            ORDER BY id ASC
        """
        df = pd.read_sql_query(query, conexao, params=(dados.get('Marca'), dados.get('Modelo'), str(dados.get('AnoModelo'))))
        conexao.close()
        
        st.divider()
        st.subheader("📊 Histórico e Variação de Preços")
               
        if not df.empty:
            produtos = df["produto"].unique()
            
            for coluna, produto in zip(st.columns(len(produtos)), produtos):
                precos = df.loc[df["produto"] == produto, "preco"]

                atual = precos.iloc[-1]
                anterior = precos.iloc[-2] if len(precos) > 1 else None
                delta = f"{atual - anterior:,.2f}" if anterior is not None else None

                with coluna:
                    st.metric(produto, f"R$ {atual:,.2f}", delta=delta)
                    st.write(f"Maior preço registrado: **R$ {precos.max():,.2f}**")
                    st.write(f"Menor preço registrado: **R$ {precos.min():,.2f}**")
    else:
        st.error(f"Erro ao buscar preço (Código {res_preco.status_code})")