# external imports
from pathlib import Path
import streamlit as st
import geopandas as gpd
import pandas as pd
import os
import plotly.graph_objects as go
from geopy.distance import geodesic
from shapely.geometry import mapping

# from streamlit_plotly_events import plotly_events
# internal imports
from plot.plot_zones import plot_zones_with_colors
from plot.Distritos import plot_borders
from Search.Search_Archives import encontrar_arquivo
from Search.Search_Diretory import encontrar_diretorio
from unidecode import unidecode
from Estabelecimentos.Funcoes_Estabelecimentos import *

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

color_map = {'lote venda': 'red', 'condominio venda': 'orange', 'lote': 'green', 'condominio': 'blue'}


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

# Carregar dados de renda média (desnecessário)
arquivo_renda = encontrar_arquivo('Renda_Por_Faixa_Distritos.xlsx')
df_renda = pd.read_excel(arquivo_renda, sheet_name='Renda Média', skiprows=1)
    # Remover acentos e converter para maiúsculas nos nomes dos distritos
df_renda['Distritos'] = df_renda['Distritos'].apply(lambda x: unidecode(str(x)).upper())
    # Converter a coluna 'Renda Média' para o formato float
df_renda['Renda Média'] = df_renda['Renda Média'].apply(lambda x: float(str(x).replace(',', '')))

# Carregar dados de domicílios por faixa de renda
arquivo_domicilios = encontrar_arquivo('Renda_Por_Faixa_Distritos.xlsx')
df_domicilios = pd.read_excel(arquivo_domicilios, sheet_name='Resultados', skiprows=0)
def convert_to_int(x):
    try:
        return int(float(x))
    except (ValueError, TypeError):
        return x
df_domicilios.iloc[:, 1:] = df_domicilios.iloc[:, 1:].map(convert_to_int)
    # Remover acentos e converter para maiúsculas nos nomes dos distritos
df_domicilios['Distritos'] = df_domicilios['Distritos'].apply(lambda x: unidecode(str(x)).upper())

# COMPONENTES DA PÁGINA
# Título
st.title('Página Principal de Filtros São Paulo')

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
    tipo_filtrado = st.multiselect('tipo lote', sorted(gdf_filtered['tipo lote'].unique()), default=gdf_filtered['tipo lote'].unique())
    gdf_filtered = gdf_filtered[gdf_filtered['tipo lote'].isin(tipo_filtrado)]

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

    # Filtro de domicílios por faixa de renda
    # Allow multiple selections for 'Faixa de Renda'
    # Adicionar a opção 'todos' no multiselect
    faixas_disponiveis = ['todos'] + list(df_domicilios.columns[2:])
    faixa_de_renda = st.selectbox('Faixa de Renda', faixas_disponiveis)

    df_domicilios_filtrado = df_domicilios[df_domicilios['Distritos'].isin(dict_regioes_possiveis[regiao_filtrada])]

    #min_domicilios = st.slider(
    #    'Número mínimo de domicílios',
    #    min_value=0,
    #    max_value=int(
    #        df_domicilios_filtrado[faixa_de_renda].max() if faixa_de_renda != 'todos' else df_domicilios.iloc[:,
    #                                                                                       2:].max().max()),
    #    value=2000
    #)

    if faixa_de_renda != 'todos':
        dict_regioes_possiveis[regiao_filtrada] = [
            distrito for distrito in dict_regioes_possiveis[regiao_filtrada]
            #if df_domicilios_filtrado[df_domicilios_filtrado['Distritos'] == distrito][faixa_de_renda].values[
            #       0] >= min_domicilios
        ]

    # Lógica de filtragem para 'todos' ou faixas de renda específicas
    if 'todos' in faixa_de_renda:
        # Sem filtragem por faixa de renda
        dict_regioes_possiveis[regiao_filtrada] = [
            distrito for distrito in dict_regioes_possiveis[regiao_filtrada]
            #if df_domicilios_filtrado[df_domicilios_filtrado['Distritos'] == distrito][
            #       df_domicilios.columns[2:]].max().max() >= min_domicilios
        ]
    else:
        # Filtragem com base nas faixas de renda selecionadas
        dict_regioes_possiveis[regiao_filtrada] = [
            distrito for distrito in dict_regioes_possiveis[regiao_filtrada]
            #if all(df_domicilios_filtrado[df_domicilios_filtrado['Distritos'] == distrito][renda].values[
            #           0] >= min_domicilios for renda in faixa_de_renda)
        ]

    # Filtro de distritos
    distritos_filtrados = st.selectbox('Distritos de Interesse', dict_regioes_possiveis[regiao_filtrada])

    # Escolha do tipo de mapa
    mapbox_style = st.selectbox('Estilo do Mapa', ['open-street-map', 'carto-positron', 'carto-darkmatter', 'satellite-streets', 'satellite'])

    # Initialize selection_df
    selection_df = pd.DataFrame()

    # Criação das abas
    tab1, tab2, tab3 = st.tabs(["Mapa de Zonas", "Estabelecimentos Próximos", "Consulta de Dados do SQL"])

    with tab1:
        # Filtrar pelo distrito selecionado
        if distritos_filtrados:
            gdf_filtered = gdf_filtered[gdf_filtered['NOME_DIST'].isin([distritos_filtrados])]
            gdf_distritos_f = sp_distritos[sp_distritos['NOME_DIST'].isin([distritos_filtrados])]

            gdf_filtered_1 = gdf_filtered[gdf_filtered['tipo lote'].isin(['lote','condominio'])]
            gdf_filtered_2 = gdf_filtered[gdf_filtered['tipo lote'].isin(['lote venda', 'condominio venda'])]
            # Criação do gráfico com custom data
            fig = plot_zones_with_colors(gdf_filtered_1, mapbox_style=mapbox_style, color_var="tipo lote",
                                         hover_data=['zl_zona','SQL'],
                                        color_discrete_map = color_map)
            if not gdf_filtered_2.empty:
                fig.add_trace(
                plot_zones_with_colors(gdf_filtered_2, mapbox_style=mapbox_style, color_var="tipo lote",
                                       hover_data=['zl_zona', 'SQL', 'Digito SQL', 'Logradouro', 'Número',
                                                   'dados venda', 'Área do Terreno (m2)', 'Testada (m)',
                                                   'Área Construída (m2)', 'Descrição do uso (IPTU)',
                                                   'Descrição do padrão (IPTU)'],
                                       color_discrete_map=color_map).data[0])

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
                selection_df = pd.DataFrame({"SQL": sqlcodes, "Latitude": latitudes, "Longitude": longitudes, "Zoneamento": zones})
                st.dataframe(selection_df.set_index('SQL'), width=5000)
            else:
                selection_df = pd.DataFrame()

    with tab2:

        def adicionar_contorno_distrito(fig, gdf_distritos_f):
            for _, row in gdf_distritos_f.iterrows():
                # Obter as coordenadas do contorno
                exterior_coords = list(mapping(row['geometry'])['coordinates'][0])

                # Separar em listas de latitude e longitude
                lat, lon = zip(*[(coord[1], coord[0]) for coord in exterior_coords])

                # Adicionar o traçado do distrito ao mapa
                fig.add_trace(go.Scattermapbox(
                    lat=list(lat),
                    lon=list(lon),
                    mode='lines',
                    line=dict(width=2, color='blue'),
                    name=row['NOME_DIST']
                ))
            return fig

        # Função para plotar os pontos no mapa
        def plotar_pontos_mapa(pontos):
            fig = go.Figure()

            for file_name, df in pontos.items():
                fig.add_trace(go.Scattermapbox(
                    lat=df['Latitude'],
                    lon=df['Longitude'],
                    mode='markers',
                    marker=dict(size=8),
                    text=file_name,
                    name=file_name
                ))

            fig.update_layout(
                mapbox_style="open-street-map",
                mapbox=dict(center=dict(lat=-23.5505, lon=-46.6333), zoom=10),
                margin={"r": 0, "t": 0, "l": 0, "b": 0}
            )
            return fig
        
        # Carregar dados de distritos e contorno de São Paulo
        sp_gdf = load_geojson(encontrar_arquivo('sao_paulo_contorno.geojson'))
        districts_gdf = sp_distritos
        # Carregar os dados das planilhas de empresas e bairros
        company_data = load_all_companies_data('data/companies')
        bairros_df = load_and_prepare_excel_data(encontrar_arquivo('bairros.xlsx'))
        arquivos_selecionados = list(company_data.keys())

        company_data = {file: filter_data_within_contour(company_data[file], file, bairros_df, sp_gdf) for file in arquivos_selecionados}
        mobility_data = load_all_companies_data('data/shapefiles/transporte/output_xlsx_files/')

        # Checkboxes para selecionar dados
        estabelecimentos_selecionados = st.checkbox('Mostrar Estabelecimentos', value=True)
        mobilidade_selecionada = st.checkbox('Mostrar Mobilidade', value=True)

        gdf_distritos_f = sp_distritos[sp_distritos['NOME_DIST'].isin([distritos_filtrados])]

        # Combinar dados com base nas seleções
        if estabelecimentos_selecionados and mobilidade_selecionada:
            dados_combined = {**company_data, **mobility_data}  # Combina os dois dicionários
        elif estabelecimentos_selecionados:
            dados_combined = company_data
        elif mobilidade_selecionada:
            dados_combined = mobility_data
        else:
            dados_combined = {}  # Nenhuma seleção feita, nenhum dado

        raio_selecao = st.slider('Definir raio de seleção (km)', min_value=0.1, max_value=50.0, step=0.1, value=5.0)

        click_data = selection_df
        click_coords = (click_data['Latitude'].values[0], click_data['Longitude'].values[0]) if not click_data.empty else None


        # Mostrar todos os pontos inicialmente
        fig = plotar_pontos_mapa(dados_combined)
        fig = adicionar_contorno_distrito(fig, gdf_distritos_f)

        # Se houver dados de clique, filtrar pontos dentro do raio e exibir o novo mapa
        if not click_data.empty:
            pontos_no_raio = {}

            # Verificar a distância de cada ponto em relação ao ponto clicado
            for file_name, df in dados_combined.items():
                pontos_filtrados = []
                for _, row in df.iterrows():
                    ponto_coords = (row['Latitude'], row['Longitude'])
                    distancia = geodesic(click_coords, ponto_coords).km
                    if distancia <= raio_selecao:
                        pontos_filtrados.append(row)

                # Adicionar ao dicionário apenas se houver pontos no raio
                if pontos_filtrados:
                    pontos_no_raio[file_name] = pd.DataFrame(pontos_filtrados)

            # Exibir o novo gráfico com pontos dentro do raio
            if pontos_no_raio:
                fig_filtrado = plotar_pontos_mapa(pontos_no_raio)
                fig_filtrado = adicionar_contorno_distrito(fig_filtrado, gdf_distritos_f)
                st.plotly_chart(fig_filtrado, use_container_width=True)
                st.write(f"Pontos encontrados dentro de {raio_selecao} km do ponto clicado:")
            else:
                st.write(f"Nenhum ponto encontrado dentro de {raio_selecao} km do ponto clicado.")
        else:
            st.write("Selecione um ponto no mapa da aba 'Mapa de Zonas' para visualizar os estabelecimentos próximos.")

    with tab3:
        # Consulta de dados
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
