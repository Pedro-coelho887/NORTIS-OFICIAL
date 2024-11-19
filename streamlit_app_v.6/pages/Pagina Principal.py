# external imports
from pathlib import Path
import streamlit as st
import geopandas as gpd
import pandas as pd
import os
import plotly.graph_objects as go
import plotly.express as px
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

st.set_page_config(layout="wide")


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

color_map = {'lote': 'green', 'condominio': 'blue'}

color_dict = {
    'Escola Privada': 'red',
    'Escola Pública': 'brown',
    'Fast Food': 'green',
    'Agencia Bancaria': 'blue',
    'Academia de Ginastica': 'yellow',
    'Faculdade': 'darkgreen',
    'Hipermercados e Supermercados': 'white',
    'Hospital': 'cyan',
    'Petshop': 'purple',
    'Restaurantes': 'orange',
    'Shopping Center': 'magenta',
    'Terminal de ônibus': 'beige',
    'Feiras Livres': 'pink'
}

distritos = encontrar_arquivo('distritos.geojson')
sp_distritos = load_and_prepare_dataframe(distritos)

# lookup zonas fora de operacao urbana NORTIS
operacao_urbana_n = encontrar_arquivo('Zonas_fora_de_operacao_urbana_att_2.xlsx')
lookup_f_op_n = pd.read_excel(operacao_urbana_n)
lookup_f_op_n["Potencial para projeto imobiliário?"] = lookup_f_op_n["Potencial para projeto imobiliário"].map(
    {1: True, 0: False})
ca_max = lookup_f_op_n['C.A Máximo'].max()
ca_min = lookup_f_op_n['C.A Máximo'].min()
gabarito_max = lookup_f_op_n['Gabarito de Altura Máxima'].max()
gabarito_min = lookup_f_op_n['Gabarito de Altura Máxima'].min()
potenciais_possiveis = lookup_f_op_n['Potencial'].unique()
territorio_possiveis = lookup_f_op_n['Território'].unique()
# lookup zonas fora de operacao urbana Vibra
operacao_urbana_v = encontrar_arquivo('Zonas_operacao_urbana_completo_Vibra.xlsx')
lookup_f_op_v = pd.read_excel(operacao_urbana_v)
lookup_f_op_v["Potencial para projeto imobiliário?"] = lookup_f_op_n["Potencial para projeto imobiliário"].map(
    {1: True, 0: False})
# ca_max_v = lookup_f_op_v['C.A Máximo'].max()
# ca_min_v = lookup_f_op_v['C.A Máximo'].min()
# gabarito_max_v = lookup_f_op_v['Gabarito de Altura Máxima'].max()
# gabarito_min_v = lookup_f_op_v['Gabarito de Altura Máxima'].min()
potenciais_possiveis_v = lookup_f_op_v['Potencial'].unique()
territorio_possiveis_v = lookup_f_op_v['Território'].unique()
#Empresas
empresas_possiveis = ['NORTIS','Vibra']
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


st.session_state.selection_df = pd.DataFrame()
st.session_state.event = None
st.session_state.buscar = False

with st.sidebar:

    # FILTROS
    filtro_empresas = st.selectbox('Empresa',empresas_possiveis,index = 0)
    filtro_potencial = st.multiselect('Potencial', potenciais_possiveis, default=potenciais_possiveis)
    if filtro_empresas == 'NORTIS':
        lookup_filtered = lookup_f_op_n[(lookup_f_op_n['Potencial'].isin(filtro_potencial))]
    elif filtro_empresas == 'Vibra':
        lookup_filtered = lookup_f_op_v[(lookup_f_op_v['Potencial'].isin(filtro_potencial))]

    #zonas_filtradas = st.selectbox('Zonas de Interesse', sorted(lookup_filtered['Tipo de Zona'].unique()))
    zonas_filtradas = st.multiselect('Zonas de Interesse', sorted(lookup_filtered['Tipo de Zona'].unique()))
    distritos_filtrados = []
    # Filtro por zonas
    if zonas_filtradas:
        gdf_filtered_list = []
    
    # Iterar sobre cada zona filtrada
        for zona in zonas_filtradas:
        # Encontrar o diretório para cada zona
            arquivo_zona_filtrada = encontrar_diretorio(zona)
        
        # Carregar os dados correspondentes
            gdf = load_and_prepare_data(arquivo_zona_filtrada)
        
        # Adicionar ao lista de dados filtrados
            gdf_filtered_list.append(gdf)
    
    # Caso queira combinar os dataframes ou manipulá-los posteriormente
        gdf_filtered = pd.concat(gdf_filtered_list, ignore_index=True)
        # Filtro de tipo
        tipo_filtrado = st.multiselect('tipo', sorted(gdf_filtered['tipo'].unique()), default=gdf_filtered['tipo'].unique())
        gdf_filtered = gdf_filtered[gdf_filtered['tipo'].isin(tipo_filtrado)]
        exibir_vendas = st.checkbox('Exibir vendas ITBI')

        distritos_possiveis = gdf_filtered['NOME_DIST'].unique()
        regioes_possiveis = []

        for distrito in distritos_possiveis:
            if distrito in centro:
                regioes_possiveis.append('centro')
            elif distrito in norte:
                regioes_possiveis.append('norte')
            elif distrito in sul:
                regioes_possiveis.append('sul')
            elif distrito in leste:
                regioes_possiveis.append('leste')
            elif distrito in oeste:
                regioes_possiveis.append('oeste')

        regioes_possiveis = list(set(regioes_possiveis))


        regiao_filtrada = st.multiselect('Regiões de Interesse', regioes_possiveis)

        distritos_em_regioes = []
        for regiao in regiao_filtrada:
            distritos_em_regioes.extend(globals()[regiao])
        distritos_possiveis = list(set(distritos_em_regioes).intersection(distritos_possiveis))

        if regiao_filtrada:
            if len(distritos_possiveis) >= 2:
                df_renda = df_renda[df_renda['Distritos'].isin(distritos_possiveis)]
                renda = st.slider('Faixa de renda', 
                          min_value=min(df_renda['Renda Média'].to_list()), 
                          max_value=max(df_renda['Renda Média'].to_list()), 
                          value=(min(df_renda['Renda Média']), max(df_renda['Renda Média'])))
        
                df_renda = df_renda[df_renda['Renda Média'].between(renda[0],renda[1])]
                distritos_renda = df_renda['Distritos'].to_list()
                distritos_possiveis = list(set(distritos_renda).intersection(distritos_possiveis))

        
        # Filtro de distritos
            distritos_filtrados = st.selectbox('Distritos de Interesse', distritos_possiveis)

        # Escolha do tipo de mapa
        mapbox_style = st.selectbox('Estilo do Mapa', ['open-street-map', 'carto-positron', 'carto-darkmatter', 'satellite-streets', 'satellite'])

        # Initialize selection_df
        selection_df = pd.DataFrame()

        # mostrar estabelecimentos
        estabelecimentos_selecionados = st.checkbox('Mostrar Estabelecimentos', value=True)

        if estabelecimentos_selecionados:
            estabelecimentos_path = encontrar_arquivo('estabelecimentos_dentro_contorno.csv')
            estabelecimentos = pd.read_csv(estabelecimentos_path)
            estabelecimentos_a_mostrar = st.multiselect('Estabelecimentos', estabelecimentos['Tipo'].unique(), default=estabelecimentos['Tipo'].unique())
            estabelecimentos = estabelecimentos[estabelecimentos['Tipo'].isin(estabelecimentos_a_mostrar)]

            # Filtro de distância
            distance = st.slider('Distância de estabelecimentos da seleção (km)', 0.1, 10.0, 1.0, 0.1)

            if st.button("Buscar estabelecimentos próximos"):
                st.session_state["buscar"] = True

if distritos_filtrados:
    if exibir_vendas:
        gdf_filtered = gdf_filtered[gdf_filtered['NOME_DIST'].isin([distritos_filtrados])]
        gdf_distritos_f = sp_distritos[sp_distritos['NOME_DIST'].isin([distritos_filtrados])]

        gdf_filtered_1 = gdf_filtered[gdf_filtered['venda'] == False]
        gdf_filtered_2 = gdf_filtered[gdf_filtered['venda'] == True]

        # Criação do gráfico com custom data
        fig = plot_zones_with_colors(gdf_filtered_1, mapbox_style=mapbox_style, color_var="tipo",
                                        hover_data=['zl_zona','SQL'],
                                    color_discrete_map = color_map)
        if not gdf_filtered_2.empty:
            color_map_2 = {True: 'red', False : 'red'}
            fig.add_trace(
            plot_zones_with_colors(gdf_filtered_2, mapbox_style=mapbox_style, color_var="venda",
                                    hover_data=['zl_zona', 'SQL', 'digito SQL', 'Nome do Logradouro', 'Número',
                                                'Bairro', 'Cartório de Registro', 'dados de vendas'],
                                    color_discrete_map = color_map_2).data[0])
    else:
        gdf_filtered = gdf_filtered[gdf_filtered['NOME_DIST'].isin([distritos_filtrados])]
        gdf_distritos_f = sp_distritos[sp_distritos['NOME_DIST'].isin([distritos_filtrados])]
        fig = plot_zones_with_colors(gdf_filtered, mapbox_style=mapbox_style, color_var="tipo",
                                        hover_data=['zl_zona','SQL'],
                                    color_discrete_map = color_map)

    fig = plot_borders(gdf_distritos_f, fig, mapbox_style=mapbox_style)

    if estabelecimentos_selecionados and not estabelecimentos.empty:                
            
        # Define a color map for different types of establishments (random)
        for tipo in estabelecimentos['Tipo'].unique():
            estabelecimento_color_map = {tipo: color_dict.get(tipo, "#000000") for tipo in estabelecimentos['Tipo'].unique()}


        # Add establishments to the map with different colors based on their type
        for tipo, color in estabelecimento_color_map.items():

            size = 16 if tipo == "Shopping Center" else 8

            filtered_estabelecimentos = estabelecimentos[estabelecimentos['Tipo'] == tipo]

            fig.add_trace(go.Scattermapbox(
                lat=filtered_estabelecimentos['Latitude'],
                lon=filtered_estabelecimentos['Longitude'],
                mode='markers',
                marker=dict(size=size, color=color, opacity=0.8),
                name=tipo.capitalize(),
                cluster={"enabled": False},
                text=filtered_estabelecimentos['Nome'] + ' '*2 + filtered_estabelecimentos['Tipo'],
                hoverinfo='text',
                selected=dict(marker=dict(opacity=0.9)),
                unselected=dict(marker=dict(opacity=0.9)),
            ))

        # Add a legend for the establishments
        fig.update_layout(showlegend=True, height=600, legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.89,
            title="Legenda",
        ))
    
    # Display the map with selection enabled
    event = st.plotly_chart(fig, on_select="rerun", selection_mode=["points", "box", "lasso"], id="map_main")

    if event:
        latitudes = []
        longitudes = []
        sqlcodes = []
        zones = []

        # Extract selected points
        for point in event.selection["points"]:
            coordinates = point.get("ct")
            sqlcode = point.get("customdata")[1]
            zone = point.get("customdata")[0]
            latitude = coordinates[1]
            longitude = coordinates[0]
            longitudes.append(longitude)
            latitudes.append(latitude)
            sqlcodes.append(sqlcode)
            zones.append(zone)

        selection_df = pd.DataFrame({
            "SQL": sqlcodes,
            "Latitude": latitudes,
            "Longitude": longitudes,
            "Zoneamento": zones
        })
        # Filtrar estabelecimentos pela distância
        filtered_estabelecimentos = filter_estabelecimentos_by_distance(estabelecimentos, selection_df, distance)

        if not filtered_estabelecimentos.empty:
            # Contagem de estabelecimentos por tipo
            count_estabelecimentos_by_type = filtered_estabelecimentos.loc[:, 'Tipo'].value_counts()

            # Encontrar o estabelecimento mais próximo para cada tipo
            closest_estabelecimento_by_type = filtered_estabelecimentos.sort_values(by=['Tipo', 'Distancia (m)'])
            closest_estabelecimento_by_type = closest_estabelecimento_by_type[
                ["Rede", "Nome", "Tipo", "Endereço", "Bairro", "Distancia (m)"]
            ].dropna(axis=1, how='all')

            # UI Melhorada
            st.subheader("Análise de Estabelecimentos")

            # Usar colunas para organizar a apresentação
            col1, col2 = st.columns(2)

            with col1:
                # Gráfico de barras para a contagem de tipos
                st.markdown("### Estabelecimentos Próximos")
                fig_count = px.bar(
                    count_estabelecimentos_by_type,
                    x=count_estabelecimentos_by_type.index,
                    y=count_estabelecimentos_by_type.values,
                    labels={'x': 'Tipo', 'y': 'Quantidade'},
                    title="Distribuição de Estabelecimentos"
                )
                st.plotly_chart(fig_count, use_container_width=True)

            with col2:
                # Seletor de Tipo de Estabelecimento
                st.subheader("Procurar por tipo")
                tipo = st.selectbox('Selecione o Tipo de Estabelecimento', filtered_estabelecimentos['Tipo'].unique())

                # Mostrar a contagem do tipo selecionado
                count_tipo = count_estabelecimentos_by_type[count_estabelecimentos_by_type.index == tipo]
                st.markdown(f"### Quantidade de {tipo}:  {count_tipo.values[0]}")

                # Mostrar os estabelecimentos mais próximos do tipo selecionado
                st.markdown(f"### Estabelecimento Mais Próximo - {tipo}")
                closest_tipo = closest_estabelecimento_by_type[closest_estabelecimento_by_type["Tipo"] == tipo]
                st.table(closest_tipo)

        


if st.button("Ver ITBI"):
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