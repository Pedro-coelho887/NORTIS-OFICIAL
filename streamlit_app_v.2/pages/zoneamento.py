# external imports
from pathlib import Path
import streamlit as st
import geopandas as gpd
import pandas as pd
import os
# internal imports
from plot.plot_zones import plot_zones_with_colors
from plot.Distritos import plot_borders
# Carregar e preparar dados

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
def load_and_prepare_data(file_path):
    gdf = gpd.read_file(file_path)
    return gdf

def gdf_to_df(gdf):
    gdf['geometry'] = gdf['geometry'].apply(lambda x: x.wkt)
    return gdf

# PROCESSAMENTO
# Carregar os dados de zonas
# sp_zonas = load_and_prepare_data(Path("data/shapefiles/zoneamento/quadras_z_d_u.shp"))
distritos = encontrar_arquivo('distritos.geojson')
sp_distritos = load_and_prepare_data(distritos)
quadras = encontrar_arquivo('quadras_z_d_u.shp')
sp_zonas = load_and_prepare_data(quadras)

operacao_urbana = encontrar_arquivo('Zonas_fora_de_operacao_urbana.xlsx')
lookup_f_op = pd.read_excel(operacao_urbana)

# lookup zonas fora de operacao urbana
#lookup_f_op = pd.read_excel(Path('data/lookups/Zonas_fora_de_operacao_urbana_att.xlsx'))
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
# Filtro de potencial
col_padding, col1, col_padding2 = st.columns([0.2,1,0.2])

with col1:
    filtro_potencial = st.multiselect('Potencial', potenciais_possiveis, default=potenciais_possiveis)

#potencial_imobiliario = st.checkbox('Mostrar apenas Zoneamentos com potencial para projeto imobiliário')
#operação_urbana = st.checkbox('Operação Urbana')

lookup_filtered = lookup_f_op[(lookup_f_op['Potencial'].isin(filtro_potencial))]
# if potencial_imobiliario:
#     lookup_filtered = lookup_filtered[lookup_filtered['Potencial para projeto imobiliário'] == True]


#Filtro de distritos
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

zonas_filtradas = st.multiselect('Zonas de Interesse', lookup_filtered['Tipo de Zona'].unique())
# Filtro por zonas
if zonas_filtradas:
    gdf_filtered = sp_zonas[sp_zonas['zl_zona'].isin(zonas_filtradas)]

    # Filtro de operações urbanas
    # if operação_urbana:
    #     gdf_filtered = gdf_filtered[gdf_filtered['OUCAB'] == True]

    #Filtro de distritos
    distritos_filtrados = st.multiselect('Distritos de Interesse',gdf_filtered['NOME_DIST'].unique())
    # Escolha do tipo de mapa
    mapbox_style = st.selectbox('Estilo do Mapa', ['open-street-map', 'carto-positron', 'carto-darkmatter'])
    if distritos_filtrados:
        gdf_filtered = gdf_filtered[gdf_filtered['NOME_DIST'].isin(distritos_filtrados)]
        gdf_distritos_f = sp_distritos[sp_distritos['NOME_DIST'].isin(distritos_filtrados)]
        fig = plot_zones_with_colors(gdf_filtered, mapbox_style=mapbox_style)
        fig_district = plot_borders(gdf_distritos_f,fig)
        st.plotly_chart(fig_district)
    else:
        # Mapa
        fig = plot_zones_with_colors(gdf_filtered, mapbox_style=mapbox_style)
        st.plotly_chart(fig)
    
# Mostrar os dados em tabela
if zonas_filtradas and st.checkbox('Mostrar dados'):
    st.table(gdf_to_df(gdf_filtered))
