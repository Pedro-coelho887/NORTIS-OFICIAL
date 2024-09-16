import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import cm
from matplotlib.colors import Normalize
from unidecode import unidecode
import os

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


# Função para plotar distritos com cores baseadas na renda
def plotar_distritos_renda(sp_gdf, distritos_gdf, df_renda, coluna_renda='Renda Média'):
    """Plota os distritos com cores baseadas na renda."""
    
    # Unir os dados de renda com os dados geográficos dos distritos
    distritos_gdf = distritos_gdf.merge(df_renda, left_on='NOME_DIST', right_on='Distritos', how='left')
    
    # Definir a normalização das cores baseada na renda
    norm = Normalize(vmin=distritos_gdf[coluna_renda].min(), vmax=distritos_gdf[coluna_renda].max())
    cmap = cm.get_cmap('coolwarm')  # Mapa de cores do azul ao vermelho
    
    # Criar o gráfico
    fig, ax = plt.subplots(figsize=(5, 5))
    
    # Plotar o contorno de São Paulo
    sp_gdf.plot(ax=ax, color='lightgrey', edgecolor='black', linewidth=1)
    
    # Plotar os distritos com as cores baseadas na renda
    distritos_gdf['color'] = distritos_gdf[coluna_renda].apply(lambda x: cmap(norm(x)))
    distritos_gdf.plot(ax=ax, color=distritos_gdf['color'], edgecolor='black')
    
    # Adicionar a legenda
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])  # Apenas para gerar a barra de cores corretamente
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label('Renda Média')
    
    # Título
    plt.title('Distritos de São Paulo pela Renda Média', fontsize=10)
    
    # Mostrar o gráfico
    st.pyplot(fig)


# Função para plotar distritos com cores baseadas nos domicílios
def plotar_distritos_domicilios(sp_gdf, distritos_gdf, df_analises, coluna_domicilios):
    """Plota os distritos com cores baseadas no número de domicílios."""
    
    # Unir os dados de análise com os dados geográficos dos distritos
    distritos_gdf = distritos_gdf.merge(df_analises, left_on='NOME_DIST', right_on='Distritos', how='left')
    
    # Definir a normalização das cores baseada no número de domicílios
    norm = Normalize(vmin=distritos_gdf[coluna_domicilios].min(), vmax=distritos_gdf[coluna_domicilios].max())
    cmap = cm.get_cmap('coolwarm')  # Mapa de cores do azul ao vermelho
    
    # Criar o gráfico
    fig, ax = plt.subplots(figsize=(5, 5))
    
    # Plotar o contorno de São Paulo
    sp_gdf.plot(ax=ax, color='lightgrey', edgecolor='black', linewidth=1)
    
    # Plotar os distritos com as cores baseadas no número de domicílios
    distritos_gdf['color'] = distritos_gdf[coluna_domicilios].apply(lambda x: cmap(norm(x)))
    distritos_gdf.plot(ax=ax, color=distritos_gdf['color'], edgecolor='black')
    
    # Adicionar a legenda
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])  # Apenas para gerar a barra de cores corretamente
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label(coluna_domicilios)
    
    # Título
    plt.title(f'Distritos pelo número de {coluna_domicilios}', fontsize=10)
    
    # Mostrar o gráfico
    st.pyplot(fig)


# Função para plotar distritos com aderência HIS² ou HMP
def plotar_distritos_aderencia(sp_gdf, distritos_gdf, df_analises, coluna_share, titulo):
    """Plota os distritos com cores baseadas na aderência (HIS² ou HMP)."""
    
    # Unir os dados de análise com os dados geográficos dos distritos
    distritos_gdf = distritos_gdf.merge(df_analises, left_on='NOME_DIST', right_on='Distritos', how='left')
    
    # Definir a lógica de aderência para HIS² ou HMP, ajustando para porcentagem
    def aderencia_classificacao(share):
        if share < 0.25:  # Considerando que os valores estão de 0 a 100
            return 'Baixo'
        elif 0.25 <= share <= 0.35:  # 25% a 35%
            return 'Médio'
        else:  # Maior que 35%
            return 'Alto'
    
    # Aplicar a classificação aos distritos
    distritos_gdf['Aderência'] = distritos_gdf[coluna_share].apply(aderencia_classificacao)
    
    # Mapa de cores para cada classificação
    distritos_gdf['color'] = distritos_gdf['Aderência'].map({'Baixo': 'green', 'Médio': 'yellow', 'Alto': 'red'})
    
    # Criar o gráfico
    fig, ax = plt.subplots(figsize=(5, 5))
    
    # Plotar o contorno de São Paulo
    sp_gdf.plot(ax=ax, color='lightgrey', edgecolor='black', linewidth=1)
    
    # Plotar os distritos com as cores baseadas na aderência
    distritos_gdf.plot(ax=ax, color=distritos_gdf['color'], edgecolor='black')
    
    # Adicionar a legenda manualmente
    baixo_patch = mpatches.Patch(color='green', label='Baixo (<25%)')
    medio_patch = mpatches.Patch(color='yellow', label='Médio (25%-35%)')
    alto_patch = mpatches.Patch(color='red', label='Alto (>35%)')
    plt.legend(handles=[baixo_patch, medio_patch, alto_patch], loc='upper right', title='Aderência')
    
    # Título
    plt.title(titulo, fontsize=10)
    
    # Mostrar o gráfico
    st.pyplot(fig)


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
