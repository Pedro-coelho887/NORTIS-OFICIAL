# external imports
from pathlib import Path
import streamlit as st
import geopandas as gpd
import pandas as pd
import os

# internal imports
from plot.plot_zones import plot_zones_with_colors
from plot.Distritos import plot_borders
from Search.Search_Archives import encontrar_arquivo
from Search.Search_Diretory import encontrar_diretorio
# Carregar e preparar dados

# Listas de distritos por regioes utilizada no filtro de regioes

centro = ['BELA VISTA', 'BOM RETIRO', 'CAMBUCI', 'CONSOLACAO', 'LIBERDADE', 'REPUBLICA', 'SANTA CECILIA', 'SE']

leste = ['ARICANDUVA', 'CARAO', 'VILA FORMOSA', 'CIDADE TIRADENTES', 'ERMELINO MATARAZZO', 'PONTE RASA', 'GUAIANASES', 
 'LAJEADO', 'ITAIM PAULISTA', 'VILA CURUCA', 'CIDADE LIDER', 'ITAQUERA', 'JOSE BONIFACIO', 'PARQUE DO CARMO', 
 'AGUA RASA', 'BELEM', 'BRAS', 'MOOCA', 'PARI', 'TATUAPE', 'ARTUR ALVIM', 'CANGAIBA', 'PENHA', 'VILA MATILDE', 
 'IGUATEMI', 'SAO MATEUS', 'SAO RAFAEL', 'JARDIM HELENA', 'SAO MIGUEL', 'VILA JACUI', 'SAO LUCAS', 'SAPOPEMBA', 
 'VILA PRUDENTE', 'CACHOEIRINHA', 'CASA VERDE']

norte = ['LIMAO', 'BRASILANDIA', 'FREGUESIA DO O', 'JACANA', 'TREMEMBE', 'ANHANGUERA', 'PERUS', 'JARAGUA', 'PIRITUBA', 
 'SAO DOMINGOS', 'MANDAQUI', 'SANTANA', 'TUCURUVI', 'VILA GUILHERME', 'VILA MARIA', 'VILA MEDEIROS']

oeste = ['BUTANTA', 'MORUMBI', 'RAPOSO TAVARES', 'RIO PEQUENO', 'VILA SONIA', 'BARRA FUNDA', 'JAGUARA', 'JAGUARE', 
 'LAPA', 'PERDIZES', 'VILA LEOPOLDINA', 'ALTO DE PINHEIROS', 'ITAIM BIBI', 'JARDIM PAULISTA', 'PINHEIROS']

sul = ['CAMPO LIMPO', 'CAPAO REDONDO', 'VILA ANDRADE', 'CIDADE DUTRA', 'GRAJAU', 'SOCORRO', 'CIDADE ADEMAR', 'PEDREIRA', 
 'CURSINO', 'IPIRANGA', 'SACOMA', 'JABAQUARA', 'JARDIM ANGELA', 'MBOI MIRIM', 'JARDIM SAO LUIS', 'MARSILAC', 
 'PARELHEIROS', 'CAMPO BELO', 'SANTO AMARO', 'CAMPO GRANDE', 'MOEMA', 'VILA MARIANA', 'SAUDE']

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
    gdf['geometry'] = gdf['geometry'].apply(lambda x: x.wkt)
    return gdf


# PROCESSAMENTO
# Carregar os dados de zonas
distritos = encontrar_arquivo('distritos.geojson')
sp_distritos = load_and_prepare_dataframe(distritos)
quadras = encontrar_diretorio('quadras_z_d_o_rng04')
sp_zonas = load_and_prepare_data(quadras)
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

# potencial_imobiliario = st.checkbox('Mostrar apenas Zoneamentos com potencial para projeto imobiliário')
# operação_urbana = st.checkbox('Operação Urbana')

lookup_filtered = lookup_f_op[(lookup_f_op['Potencial'].isin(filtro_potencial))]

zonas_filtradas = st.selectbox('Zonas de Interesse', lookup_filtered['Tipo de Zona'].unique())
# Filtro por zonas

if zonas_filtradas:
    
    gdf_filtered = sp_zonas[sp_zonas['zl_zona'].isin([zonas_filtradas])]
    
    distritos_possiveis = gdf_filtered['NOME_DIST'].unique()
    print(distritos_possiveis)
    # Filtro de regioes
    
    dict_regioes_possiveis = {'Centro': [], 'Norte': [], 'Sul': [], 'Leste': [], 'Oeste': []}
    
    for distrito in distritos_possiveis:
        if distrito in centro:
            dict_regioes_possiveis['Centro'].append(distrito)
        elif distrito in norte:
            dict_regioes_possiveis['Norte'].append(distrito)
        elif distrito in sul:
            dict_regioes_possiveis['Sul'].append(distrito)
        elif distrito in leste:
            dict_regioes_possiveis['Leste'].append(distrito)
        elif distrito in oeste:
            dict_regioes_possiveis['Oeste'].append(distrito)
    
    regioes_possiveis = [key for key in dict_regioes_possiveis.keys() if len(dict_regioes_possiveis[key]) > 0 ]
    
    regiao_filtrada = st.radio('Regioes de Interesse', regioes_possiveis)

    # Filtro de distritos
    
    distritos_filtrados = st.multiselect('Distritos de Interesse', dict_regioes_possiveis[regiao_filtrada])

    
    # Escolha do tipo de mapa
    mapbox_style = st.selectbox('Estilo do Mapa', ['open-street-map', 'carto-positron', 'carto-darkmatter'])
    if distritos_filtrados:
        gdf_filtered = gdf_filtered[gdf_filtered['NOME_DIST'].isin(distritos_filtrados)]
        gdf_distritos_f = sp_distritos[sp_distritos['NOME_DIST'].isin(distritos_filtrados)]
        fig = plot_zones_with_colors(gdf_filtered, mapbox_style=mapbox_style)
        fig_district = plot_borders(gdf_distritos_f, fig)
        st.plotly_chart(fig_district)
    else:
        # Mapa
        fig = plot_zones_with_colors(gdf_filtered, mapbox_style=mapbox_style)
        st.plotly_chart(fig)

# Mostrar os dados em tabela
if zonas_filtradas and st.checkbox('Mostrar dados'):
    st.table(gdf_to_df(gdf_filtered))
