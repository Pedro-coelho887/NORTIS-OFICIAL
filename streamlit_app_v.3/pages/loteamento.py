# external imports
from pathlib import Path
import streamlit as st
import geopandas as gpd
import pandas as pd
import os
# internal imports
from plot.plot_zones import plot_zones_with_colors
from plot.Distritos import plot_borders

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
# Carregar e preparar dados
@st.cache_data
def load_and_prepare_data(directory_path):
    # Lista para armazenar os GeoDataFrames
    gdf_list = []

    # Iterar sobre os arquivos no diretório
    for filename in os.listdir(directory_path):
        if filename.endswith('.geojson') or filename.endswith('.shp'):  # Verifique as extensões necessárias
            file_path = os.path.join(directory_path, filename)
            gdf = gpd.read_file(file_path)  # Carregar o GeoDataFrame
            gdf_list.append(gdf)  # Adicionar o GeoDataFrame à lista

    # Concatenar todos os GeoDataFrames em um único
    combined_gdf = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True))

    return combined_gdf

def load_and_prepare_dataframe(directory_path):
    gdf = gpd.read_file(directory_path)
    return gdf

def gdf_to_df(gdf):
    gdf = gdf.drop(columns = ['geometry'])
    return gdf

distritos = encontrar_arquivo('distritos.geojson')
sp_distritos = load_and_prepare_dataframe(distritos)
# lookup zonas fora de operacao urbana
operacao_urbana = encontrar_arquivo('Zonas_fora_de_operacao_urbana_att_2.xlsx')
lookup_f_op = pd.read_excel(operacao_urbana)
lookup_f_op["Potencial para projeto imobiliário?"] = lookup_f_op["Potencial para projeto imobiliário"].map(
    {1: True, 0: False})
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
# Filtro de potencial
col_padding, col1, col_padding2 = st.columns([0.2, 1, 0.2])

with col1:
    filtro_potencial = st.multiselect('Potencial', potenciais_possiveis, default=potenciais_possiveis)



lookup_filtered = lookup_f_op[(lookup_f_op['Potencial'].isin(filtro_potencial))]
# if potencial_imobiliario:
#     lookup_filtered = lookup_filtered[lookup_filtered['Potencial para projeto imobiliário'] == True]


# Filtro de distritos
# distritos_filtrados = st.multiselect('Distritos de Interesse',sp_zonas['NOME_DIST'].unique())
# =======
# zonas_filtradas = st.multiselect('Zonas de Interesse', lookup_filtered['Tipo de Zona'].unique())
# # Filtro por zonas
# if zonas_filtradas:
#     gdf_filtered = sp_zonas[sp_zonas['zl_zona'].isin(zonas_filtradas)]
#
#     #Filtro de distritos
#     distritos_filtrados = st.multiselect('Distritos de Interesse',gdf_filtered['NOME_DIST'].unique())
#
#     if distritos_filtrados:
#         gdf_filtered = gdf_filtered[gdf_filtered['NOME_DIST'].isin(distritos_filtrados)]

zonas_filtradas = st.selectbox('Zonas de Interesse', sorted(lookup_filtered['Tipo de Zona'].unique()))
# Filtro por zonas
if zonas_filtradas:
    gdf_filtered = load_and_prepare_data('data/shapefiles/loteamento/' + str(zonas_filtradas))
    # Filtro de operações urbanas
    # if operação_urbana:
    #     gdf_filtered = gdf_filtered[gdf_filtered['OUCAB'] == True]

    # Filtro de distritos
    distritos_filtrados = st.selectbox('Distritos de Interesse', sorted(gdf_filtered['NOME_DIST'].unique()))
    # Escolha do tipo de mapa
    mapbox_style = st.selectbox('Estilo do Mapa', ['open-street-map', 'carto-positron', 'carto-darkmatter','satellite-streets','satellite'])
    if distritos_filtrados:
        gdf_filtered = gdf_filtered[gdf_filtered['NOME_DIST'].isin([distritos_filtrados])]
        gdf_distritos_f = sp_distritos[sp_distritos['NOME_DIST'].isin([distritos_filtrados])]
        fig = plot_zones_with_colors(gdf_filtered, mapbox_style=mapbox_style,color_var="tipo",hover_data=["zl_zona","SQL"])
        fig_district = plot_borders(gdf_distritos_f, fig, mapbox_style=mapbox_style)
        st.plotly_chart(fig)
    else:
        # Mapa
        fig = plot_zones_with_colors(gdf_filtered, mapbox_style=mapbox_style,color_var="tipo",hover_data=["zl_zona","SQL"])
        st.plotly_chart(fig)

# Mostrar os dados em tabela
if zonas_filtradas and st.checkbox('Mostrar dados'):
    st.table(gdf_to_df(gdf_filtered))
