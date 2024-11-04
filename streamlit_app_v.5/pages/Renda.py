import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import cm
from matplotlib.colors import Normalize
import unidecode
import os
import plotly.express as px
import plotly.graph_objects as go

def encontrar_arquivo(nome_arquivo, pasta_inicial=None):
    """
    Procura por um arquivo a partir de um diretório inicial, pesquisando em todas as subpastas.
    
    Parâmetros:
    - nome_arquivo (str): O nome do arquivo a ser encontrado.
    - pasta_inicial (str, opcional): O caminho da pasta inicial onde começar a busca. Se None, usa o diretório atual.
    
    Retorna:
    - O caminho completo do arquivo encontrado, ou None se não for encontrado.
    """
    if pasta_inicial is None:
        pasta_inicial = os.getcwd()  # Usa a pasta atual se nenhuma for especificada

    # Percorre recursivamente todas as pastas e subpastas
    for raiz, pastas, arquivos in os.walk(pasta_inicial):
        if nome_arquivo in arquivos:
            return os.path.join(raiz, nome_arquivo)
    
    return None  # Se o arquivo não for encontrado

# Função para carregar dados de renda e unir com os distritos
def carregar_dados_renda(arquivo_excel, sheet_name):
    """Carrega os dados de renda e retorna um DataFrame."""
    df_renda = pd.read_excel(arquivo_excel, sheet_name=sheet_name, skiprows=1)
    
    # Remover acentos e converter para maiúsculas nos nomes dos distritos
    df_renda['Distritos'] = df_renda['Distritos'].apply(lambda x: unidecode(str(x)).upper())
    
    # Converter a coluna 'Renda Média' para o formato float
    df_renda['Renda Média'] = df_renda['Renda Média'].apply(lambda x: float(str(x).replace('.', '').replace(',', '.')))
    
    return df_renda

# Função para carregar dados de renda e unir com os distritos
def carregar_outras_analises(arquivo_excel, sheet_name='Outras Análises'):
    """Carrega os dados de renda e retorna um DataFrame."""
    outras_analises = pd.read_excel(arquivo_excel, sheet_name=sheet_name)
    
    # Remover acentos e converter para maiúsculas nos nomes dos distritos
    outras_analises['Distritos'] = outras_analises['Distritos'].apply(lambda x: unidecode(str(x)).upper())
    
    # Converter a coluna 'Renda Média' para o formato float
    #outras_analises['Renda Média'] = outras_analises['Renda Média'].apply(lambda x: float(str(x).replace('.', '').replace(',', '.')))
    
    #outras_analises['Share HIS'] = outras_analises['Share HIS'].replace('%', '')
    #outras_analises['Share HMP'] = outras_analises['Share HMP'].replace('%', '')


    return outras_analises

# Função para plotar distritos com cores baseadas na renda usando Plotly
def plotar_distritos_renda(sp_gdf, distritos_gdf, df_renda, coluna_renda='Renda Média'):
    """Plota os distritos com cores baseadas na renda usando Plotly."""
    
    # Unir os dados de renda com os dados geográficos dos distritos
    distritos_gdf = distritos_gdf.merge(df_renda, left_on='NOME_DIST', right_on='Distritos', how='left')
    
    # Criar o gráfico com Plotly usando uma escala de cores válida, como 'viridis'
    fig = px.choropleth(
        distritos_gdf, 
        geojson=distritos_gdf.geometry, 
        locations=distritos_gdf.index, 
        color=coluna_renda,
        hover_name='NOME_DIST',
        color_continuous_scale='viridis',  # Alterar para uma escala de cores válida
        labels={coluna_renda: 'Renda Média'}
    )
    
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(title_text='Distritos de São Paulo pela Renda Média')
    
    # Mostrar o gráfico
    st.plotly_chart(fig)

# Função para plotar distritos com cores baseadas no número de domicílios usando Plotly
def plotar_distritos_domicilios(sp_gdf, distritos_gdf, df_analises, coluna_domicilios):
    """Plota os distritos com cores baseadas no número de domicílios usando Plotly."""
    
    # Unir os dados de análise com os dados geográficos dos distritos
    distritos_gdf = distritos_gdf.merge(df_analises, left_on='NOME_DIST', right_on='Distritos', how='left')
    
    # Criar o gráfico com Plotly, usando uma escala de cores válida
    fig = px.choropleth(
        distritos_gdf, 
        geojson=distritos_gdf.geometry, 
        locations=distritos_gdf.index, 
        color=coluna_domicilios,
        hover_name='NOME_DIST',
        color_continuous_scale=px.colors.sequential.Viridis,  # Alterar para uma escala válida no Plotly
        labels={coluna_domicilios: coluna_domicilios}
    )
    
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(title_text=f'Distritos pelo número de {coluna_domicilios}')
    
    # Mostrar o gráfico
    st.plotly_chart(fig)


# Função para plotar distritos com aderência HIS² ou HMP usando Plotly
def plotar_distritos_aderencia(sp_gdf, distritos_gdf, df_analises, coluna_share, titulo):
    """Plota os distritos com cores baseadas na aderência (HIS² ou HMP) usando Plotly."""
    
    # Unir os dados de análise com os dados geográficos dos distritos
    distritos_gdf = distritos_gdf.merge(df_analises, left_on='NOME_DIST', right_on='Distritos', how='left')
    
    # Definir a lógica de aderência para HIS² ou HMP, ajustando para porcentagem
    def aderencia_classificacao(share):
        if share < 0.25:
            return 'Baixo'
        elif 0.25 <= share <= 0.35:
            return 'Médio'
        else:
            return 'Alto'
    
    # Aplicar a classificação aos distritos
    distritos_gdf['Aderência'] = distritos_gdf[coluna_share].apply(aderencia_classificacao)
    
    # Criar o gráfico com Plotly
    fig = px.choropleth(
        distritos_gdf, 
        geojson=distritos_gdf.geometry, 
        locations=distritos_gdf.index, 
        color='Aderência',
        hover_name='NOME_DIST',
        color_discrete_map={'Baixo': 'green', 'Médio': 'yellow', 'Alto': 'red'},
        labels={'Aderência': 'Aderência'}
    )
    
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(title_text=titulo)
    
    # Mostrar o gráfico
    st.plotly_chart(fig)


# Caminhos para os arquivos
sao_paulo_geojson = encontrar_arquivo('sao_paulo_contorno.geojson')
distritos_geojson = encontrar_arquivo('distritos.geojson')
arquivo_renda = encontrar_arquivo('Renda_Por_Faixa_Distritos.xlsx')

# Carregar os GeoJSON e os dados de renda
sp_gdf = gpd.read_file(sao_paulo_geojson)
distritos_gdf = gpd.read_file(distritos_geojson)
df_renda = carregar_dados_renda(arquivo_renda, 'Renda Média')

# Carregar os dados de outras análises
outras_analises = carregar_outras_analises(arquivo_renda, 'Outras Análises')

# Interface de seleção de gráficos
opcoes = st.multiselect(
    'Selecione os gráficos que deseja visualizar:',
    ['Renda Média', 'Total de Domicílios', 'Domicílios HIS', 'Domicílios HMP', 'Aderência HIS²', 'Aderência HMP'],
    default=['Renda Média', 'Total de Domicílios', 'Domicílios HIS', 'Domicílios HMP', 'Aderência HIS²', 'Aderência HMP']
)

# Plotar gráficos com base na seleção
if 'Renda Média' in opcoes:
    plotar_distritos_renda(sp_gdf, distritos_gdf, df_renda)

if 'Total de Domicílios' in opcoes:
    plotar_distritos_domicilios(sp_gdf, distritos_gdf, outras_analises, 'Total de Domicílios')

if 'Domicílios HIS' in opcoes:
    plotar_distritos_domicilios(sp_gdf, distritos_gdf, outras_analises, 'Domicílios HIS')

if 'Domicílios HMP' in opcoes:
    plotar_distritos_domicilios(sp_gdf, distritos_gdf, outras_analises, 'Domicílios HMP')

if 'Aderência HIS²' in opcoes:
    plotar_distritos_aderencia(sp_gdf, distritos_gdf, outras_analises, 'Share HIS', 'Aderência HIS')

if 'Aderência HMP' in opcoes:
    plotar_distritos_aderencia(sp_gdf, distritos_gdf, outras_analises, 'Share HMP', 'Aderência HMP')
