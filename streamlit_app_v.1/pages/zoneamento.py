# external imports
from pathlib import Path
import streamlit as st
import geopandas as gpd
import pandas as pd
import os
# internal imports
from plot.plot_zones import plot_zones_with_colors

# Carregar e preparar dados
def load_and_prepare_data(file_path):
    gdf = gpd.read_file(file_path)
    return gdf

def gdf_to_df(gdf):
    gdf['geometry'] = gdf['geometry'].apply(lambda x: x.wkt)
    return gdf


def encontrar_arquivo(nome_arquivo):
    # Começa na pasta atual se nenhuma for especificada
    pasta_inicial = os.path.abspath(os.path.dirname(__file__))

    # Lista de pastas a verificar, começando pela inicial
    pastas_a_verificar = []

    # Subir até a raiz, adicionando cada pasta à lista
    while True:
        pastas_a_verificar.append(pasta_inicial)

        # Se já estivermos na raiz, interrompe o loop
        nova_pasta = os.path.dirname(pasta_inicial)
        if nova_pasta == pasta_inicial:  # Isso significa que já estamos na raiz
            break

        pasta_inicial = nova_pasta

    # Agora, desce recursivamente a partir da raiz
    for pasta in pastas_a_verificar:
        for raiz, subpastas, arquivos in os.walk(pasta):
            if nome_arquivo in arquivos:
                return os.path.join(raiz, nome_arquivo)

    return None  # Arquivo não encontrado


# PROCESSAMENTO
# Carregar os dados de zonas
raiz = os.path.dirname(os.path.abspath(__file__))

quadras = encontrar_arquivo('quadras_z_d_u.shp')
sp_zonas = load_and_prepare_data(quadras)
# lookup zonas fora de operacao urbana
operacao_urbana = encontrar_arquivo('Zonas_fora_de_operacao_urbana.xlsx')
lookup_f_op = pd.read_excel(operacao_urbana)


lookup_f_op["Potencial para projeto imobiliário?"] = lookup_f_op["Potencial para projeto imobiliário"].map({1: True, 0: False})
ca_max = lookup_f_op['C.A Máximo'].max()
ca_min = lookup_f_op['C.A Máximo'].min()
gabarito_max = lookup_f_op['Gabarito de Altura Máxima'].max()
gabarito_min = lookup_f_op['Gabarito de Altura Máxima'].min()
potenciais_possiveis = lookup_f_op['Potencial'].unique()
territorio_possiveis = lookup_f_op['Território'].unique()


# COMPONENTES DA PÁGINA
# Título
st.title('Mapa de Zoneamento de São Paulo')

# FILTROS
# Filtros de potencial e território
col1, col_padding, col2 = st.columns([1, 0.05, 1])
with col1:
    filtro_potencial = st.multiselect('Potencial', potenciais_possiveis, default=potenciais_possiveis)
with col2:
    filtro_territorio = st.multiselect('Território', territorio_possiveis, default=territorio_possiveis)
# checkbox de potencial para projeto imobiliário
potencial_imobiliario = st.checkbox('Mostrar apenas Zoneamentos com potencial para projeto imobiliário')
operação_urbana = st.checkbox('Operação Urbana')

lookup_filtered = lookup_f_op[(lookup_f_op['Potencial'].isin(filtro_potencial)) &
                                (lookup_f_op['Território'].isin(filtro_territorio))]
if potencial_imobiliario:
    lookup_filtered = lookup_filtered[lookup_filtered['Potencial para projeto imobiliário'] == True]

# Filtro de zonas
zonas_filtradas = st.multiselect('Zonas de Interesse', lookup_filtered['Tipo de Zona'].unique())
# filter gdf by zonas_filtradas
gdf_filtered = sp_zonas[sp_zonas['zl_zona'].isin(zonas_filtradas)]
#Filtro de operações urbanas
if operação_urbana:
    gdf_filtered = gdf_filtered[gdf_filtered['OUCAB'] == True]

#Filtro de distritos
distritos_filtrados = st.multiselect('Distritos de Interesse',gdf_filtered['NOME_DIST'].unique())

if distritos_filtrados:
    gdf_filtered = gdf_filtered[gdf_filtered['NOME_DIST'].isin(distritos_filtrados)]



# Escolha do tipo de mapa
mapbox_style = st.selectbox('Estilo do Mapa', ['open-street-map', 'carto-positron', 'carto-darkmatter'])
# Mapa
if zonas_filtradas:
    fig = plot_zones_with_colors(gdf_filtered, mapbox_style=mapbox_style)
    st.plotly_chart(fig)
    
# Mostrar os dados em tabela
if zonas_filtradas and st.checkbox('Mostrar dados'):
    st.table(gdf_to_df(gdf_filtered))
