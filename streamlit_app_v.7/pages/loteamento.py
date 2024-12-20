# external imports
from pathlib import Path
import streamlit as st
import geopandas as gpd
import pandas as pd
import os
# from streamlit_plotly_events import plotly_events
# internal imports
from plot.plot_zones import plot_zones_with_colors
from plot.Distritos import plot_borders
from Search.Search_Archives import encontrar_arquivo
from Search.Search_Diretory import encontrar_diretorio

# Carregar e preparar dados
@st.cache_data
def load_and_prepare_data(directory_path):
    # Lista para armazenar os GeoDataFrames
    gdf_list = []

    # Iterar sobre os arquivos no diretório
    for filename in os.listdir(directory_path):
        if filename.endswith('.geojson') or filename.endswith('.shp'): # Verifique as extensões necessárias
            file_path = os.path.join(directory_path, filename)
            gdf = gpd.read_file(file_path)  # Carregar o GeoDataFrame
            gdf_list.append(gdf)  # Adicionar o GeoDataFrame à lista

    # Concatenar todos os GeoDataFrames em um único
    combined_gdf = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True))
    combined_gdf.loc[combined_gdf['tipo'] == 'venda','teste'] = 'dskdjsakDSAKDHSAKJDSAUDGSAIDUYSADISAHDKSJHDKASJHDSAKJDHSAKJDHSKJDHSAKDJSHADKJSAHDKJSHDSAKJDHSAKJDHSKDJHSADKJHASj <br> djsakdjsakdj <br> dsadsadksjdak'
    return combined_gdf

def load_and_prepare_dataframe(directory_path):
    gdf = gpd.read_file(directory_path)
    return gdf

def gdf_to_df(gdf):
    gdf = gdf.drop(columns = ['geometry'])
    return gdf

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

color_map = {'venda': 'red', 'lote': 'blue', 'condominio': 'orange'}


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
# Filtro e potencial
col_padding, col1, col_padding2 = st.columns([0.2, 1, 0.2])

with col1:
    filtro_potencial = st.multiselect('Potencial', potenciais_possiveis, default=potenciais_possiveis)

lookup_filtered = lookup_f_op[(lookup_f_op['Potencial'].isin(filtro_potencial))]

zonas_filtradas = st.selectbox('Zonas de Interesse', sorted(lookup_filtered['Tipo de Zona'].unique()))
# Filtro por zonas
if zonas_filtradas:
    arquivo_zona_filtrada = encontrar_diretorio(str(zonas_filtradas))
    gdf_filtered = load_and_prepare_data(arquivo_zona_filtrada)

    # Filtro de tipo
    tipo_filtrado = st.multiselect('Tipo', sorted(gdf_filtered['tipo'].unique()), default=gdf_filtered['tipo'].unique())
    gdf_filtered = gdf_filtered[gdf_filtered['tipo'].isin(tipo_filtrado)]

    distritos_possiveis = gdf_filtered['NOME_DIST'].unique()
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

    regioes_possiveis = [key for key in dict_regioes_possiveis.keys() if len(dict_regioes_possiveis[key]) > 0]

    regiao_filtrada = st.radio('Regiões de Interesse', regioes_possiveis)

    # Filtro de distritos
    distritos_filtrados = st.selectbox('Distritos de Interesse', dict_regioes_possiveis[regiao_filtrada])

    # Escolha do tipo de mapa
    mapbox_style = st.selectbox('Estilo do Mapa', ['open-street-map', 'carto-positron', 'carto-darkmatter', 'satellite-streets', 'satellite'])

    # Filtrar pelo distrito selecionado
    if distritos_filtrados:
        gdf_filtered = gdf_filtered[gdf_filtered['NOME_DIST'].isin([distritos_filtrados])]
        gdf_distritos_f = sp_distritos[sp_distritos['NOME_DIST'].isin([distritos_filtrados])]

        # Criação do gráfico com custom data
        fig = plot_zones_with_colors(gdf_filtered, mapbox_style=mapbox_style, color_var="tipo",
                                     hover_data=['zl_zona','SQL','Digito SQL', 'Logradouro','Número',
                                                 'dados venda','Área do Terreno (m2)','Testada (m)','Área Construída (m2)',
                                                 'Descrição do uso (IPTU)','Descrição do padrão (IPTU)'],
                                    color_discrete_map = color_map)
        fig = plot_borders(gdf_distritos_f, fig, mapbox_style=mapbox_style)
        
        event = st.plotly_chart(fig, on_select="rerun", selection_mode=["points","box","lasso"])

        if event:
            latitudes = []
            longitudes = []
            sqlcodes = []
            zones = []
            for point in event.selection["points"]:
                coordinates = point.get("ct")
                sqlcode = point.get("customdata")[1]
                zone = point.get("customdata")[0]
                latitude = coordinates[1]
                longitude = coordinates[0]
                latitudes.append(latitude)
                longitudes.append(longitude)
                sqlcodes.append(sqlcode)
                zones.append(zone)

            # make a dataframe and show it as a table with cols sql, lat and lon
            df = pd.DataFrame({"SQL": sqlcodes, "Latitude": latitudes, "Longitude": longitudes, "Zoneamento": zones})
            st.dataframe(df.set_index('SQL'), width=5000)
            


@st.cache_data
def read_ITBI(path):

    return pd.read_excel(path)

ITBI = encontrar_arquivo('tabelas_tratadas_ITBI.xlsx')
df = read_ITBI(ITBI)

codigo_input = st.text_input('Insira o SQL para pesquisa')

if codigo_input:
    try:
        codigo_input = str(codigo_input)
        # Filtra o dataframe para exibir os dados do código
        resultado = df[df['SQL'] == codigo_input]

        if not resultado.empty:
            # Exibe os dados do código
            st.write('Dados do código encontrado:')
            st.dataframe(resultado)
        else:
            st.warning('Código não encontrado.')
    except ValueError:
        st.error('Por favor, insira um código numérico válido.')