# External imports
from pathlib import Path
import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import random
import os
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import DBSCAN
import numpy as np
from geopy.distance import great_circle
from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString
from Estabelecimentos.Funcoes_Estabelecimentos import *
from Search.Search_Archives import encontrar_arquivo

st.title('Estabelecimentos por agrupamento')

# Slider global para a distância de agrupamento
distancia_agrupamento = st.slider(
    'Distância para agrupar (em km)', 
    min_value=0.0, 
    max_value=50.0, 
    step=1.0, 
    value=5.0,
    key = 1, 
)

# Atualizando a função de plotagem
def plot_points_and_districts_with_contour(filtered_data, sp_gdf, districts_gdf, color_dict):
    fig = go.Figure()

    # Gerar a tabela dos 10 distritos com mais pontos
    top_districts_table = generate_top_districts_table(filtered_data, districts_gdf)
    top_districts = top_districts_table['Distrito'].tolist()

    # Verificar se a geometria de São Paulo é Polygon ou MultiPolygon
    sp_geometry = sp_gdf.geometry.iloc[0]
    if sp_geometry.geom_type in ['Polygon', 'MultiPolygon']:
        if sp_geometry.geom_type == 'Polygon':
            lat = list(sp_geometry.exterior.xy[1])
            lon = list(sp_geometry.exterior.xy[0])
        else:
            lat = list(sp_geometry.geoms[0].exterior.xy[1])
            lon = list(sp_geometry.geoms[0].exterior.xy[0])

        sp_contour_trace = go.Scattermapbox(
            lat=lat,
            lon=lon,
            mode='lines',
            line=dict(width=2, color='black'),
            name="Contorno São Paulo"
        )
        fig.add_trace(sp_contour_trace)

    # Plotar apenas os 10 distritos com mais pontos
    districts_to_plot = districts_gdf[districts_gdf['NOME_DIST'].isin(top_districts)]

    for idx, row in districts_to_plot.iterrows():
        district_boundary = row['geometry'].boundary

        # Verificar o tipo de geometria e tratá-la adequadamente
        if isinstance(district_boundary, (Polygon, MultiPolygon)):
            if district_boundary.geom_type == 'Polygon':
                lat = list(district_boundary.exterior.xy[1])
                lon = list(district_boundary.exterior.xy[0])
            else:
                lat = list(district_boundary.geoms[0].exterior.xy[1])
                lon = list(district_boundary.geoms[0].exterior.xy[0])

        elif isinstance(district_boundary, (LineString, MultiLineString)):
            # Para LineString ou MultiLineString, acessar diretamente as coordenadas
            if district_boundary.geom_type == 'LineString':
                lat, lon = district_boundary.xy[1], district_boundary.xy[0]
            else:
                lat, lon = district_boundary.geoms[0].xy[1], district_boundary.geoms[0].xy[0]

        district_trace = go.Scattermapbox(
            lat=list(lat),
            lon=list(lon),
            mode='lines',
            line=dict(width=1, color='blue'),
            name=row['NOME_DIST']
        )
        fig.add_trace(district_trace)
    
    # Ajuste no tamanho das bolhas para agrupamento/desagrupamento
    bubble_size_clustered = 25  # Tamanho fixo para bolhas agrupadas
    bubble_size_unclustered = 15  # Tamanho menor para pontos individuais

    # Plotar pontos agrupados ou desagrupados
    for file_name, gdf in filtered_data.items():
        if not gdf.empty:
            clustered_gdf = cluster_points(gdf, distancia_agrupamento)
            clustered_gdf = assign_districts_to_points(clustered_gdf, districts_gdf)

            # Agrupar se a distância for maior que 0, caso contrário, desagrupar
            if distancia_agrupamento > 0:
                clustered_gdf['hover_text'] = clustered_gdf.apply(
                    lambda row: f"Cluster de {row['Num_Points']} pontos<br>Estabelecimento: {row['Estabelecimento']}<br>Distrito: {row['NOME_DIST']}", axis=1
                )
            else:
                clustered_gdf['Num_Points'] = 1
                clustered_gdf['hover_text'] = clustered_gdf.apply(
                    lambda row: f"Ponto único<br>Estabelecimento: {row['Estabelecimento']}<br>Distrito: {row['NOME_DIST']}", axis=1
                )

            points_trace = go.Scattermapbox(
                lat=clustered_gdf['Latitude'],
                lon=clustered_gdf['Longitude'],
                mode='markers+text',  # Adicione '+text' para exibir o texto
                marker=dict(
                    size=bubble_size_clustered if distancia_agrupamento > 0 else bubble_size_unclustered,
                    color=color_dict.get(file_name, 'blue'),
                    opacity=0.6
                ),
                name=f"{file_name} ({'agrupado' if distancia_agrupamento > 0 else 'desagrupado'})",
                text=clustered_gdf['Num_Points'].astype(str),  # Mostra o número de estabelecimentos agrupados
                textposition="middle center",  # Posição do texto no centro da bolha
                hoverinfo='text'
            )
            fig.add_trace(points_trace)

    # Configurações de layout
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=10,
        mapbox_center={"lat": -23.55052, "lon": -46.633308},
        height=600,
        title="Pontos Agrupados de Estabelecimentos e Distritos em São Paulo",
        margin={"r": 0, "t": 50, "l": 0, "b": 0}
    )

    st.plotly_chart(fig)

# Função para gerar uma tabela dos 10 distritos com mais pontos
def generate_top_districts_table(filtered_data, districts_gdf):
    # Inicializar um dicionário para contar os pontos por distrito
    district_point_count = {district: 0 for district in districts_gdf['NOME_DIST']}
    
    # Contar quantos pontos estão dentro de cada distrito
    for _, gdf in filtered_data.items():
        for _, point in gdf.iterrows():
            point_geom = gpd.points_from_xy([point['Longitude']], [point['Latitude']])[0]
            for district, geom in zip(districts_gdf['NOME_DIST'], districts_gdf['geometry']):
                if point_geom.within(geom):
                    district_point_count[district] += 1

    # Ordenar os distritos com mais pontos e retornar os 10 primeiros
    sorted_districts = sorted(district_point_count.items(), key=lambda item: item[1], reverse=True)[:10]
    return pd.DataFrame(sorted_districts, columns=['Distrito', 'Número de Pontos'])

# Carregar dados de distritos e contorno de São Paulo
sp_gdf = load_geojson(encontrar_arquivo('sao_paulo_contorno.geojson'))
districts_gdf = load_geojson(encontrar_arquivo('distritos.geojson'))

# Carregar os dados das planilhas de empresas e bairros
company_data = load_all_companies_data('data/companies')
bairros_df = load_and_prepare_excel_data(encontrar_arquivo('bairros.xlsx'))

# Sidebar para escolher os arquivos e distritos
#selected_files = st.sidebar.multiselect("Escolha os arquivos para plotar", list(company_data.keys()))
#selected_districts = st.sidebar.multiselect("Escolha os distritos para plotar", districts_gdf['NOME_DIST'].unique().tolist(), default=districts_gdf['NOME_DIST'].unique().tolist())

# Sidebar para escolher os arquivos e distritos
selected_files = st.multiselect("Escolha os arquivos para plotar", list(company_data.keys()))
selected_districts = districts_gdf['NOME_DIST'].unique().tolist()

# Definir cores para os pontos de empresas
color_dict = {
    'Escola Privada': 'red',
    'Escola Pública': 'brown',
    'Fast Food': 'green',
    'Agencia Bancaria': 'blue',
    'Academia de Ginastica': 'yellow',
    'Faculdade': 'black',
    'Hipermercados e Supermercados': 'white',
    'Hospital': 'cyan',
    'Petshop': 'purple',
    'Restaurantes': 'orange',
    'Shopping Center': 'magenta',
    'Terminal de ônibus': 'beige',
    'Feiras Livres': 'pink'
}

# Filtrar os dados escolhidos
filtered_data = {file: filter_data_within_contour(company_data[file], file, bairros_df, sp_gdf) for file in selected_files}

# Plotar pontos e distritos (remova 'selected_districts')
if any(not df.empty for df in filtered_data.values()):
    plot_points_and_districts_with_contour(filtered_data, sp_gdf, districts_gdf, color_dict)
    
    # Gerar a tabela dos 10 distritos com mais pontos
    top_districts_table = generate_top_districts_table(filtered_data, districts_gdf)
    st.write("Top 10 Distritos com Mais Pontos:")
    st.dataframe(top_districts_table)
else:
    st.warning("Nenhum dado válido encontrado para plotar.")

st.title('Estabelecimentos numa região')
import plotly.graph_objects as go
from geopy.distance import geodesic
import pandas as pd

# Carregar os dados das empresas e dos bairros
arquivos_selecionados = list(company_data.keys())
bairros_df = load_and_prepare_excel_data(encontrar_arquivo('bairros.xlsx'))
company_data = {file: filter_data_within_contour(company_data[file], file, bairros_df, sp_gdf) for file in arquivos_selecionados}


# Slider para definir o raio de seleção (em km)
raio_selecao = st.slider('Definir raio de seleção (km)', min_value=0.1, max_value=50.0, step=0.1, value=5.0)

# Definir o modo de seleção com um botão
if 'selection_mode' not in st.session_state:
    st.session_state.selection_mode = False

if st.button('Ativar modo de seleção de pontos'):
    st.session_state.selection_mode = not st.session_state.selection_mode

# Variável para armazenar dados de clique do mapa
click_data = None

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

# Mostrar todos os pontos inicialmente
fig = plotar_pontos_mapa(company_data)

# Verificar se o modo de seleção foi ativado
if st.session_state.selection_mode:
    st.info("Clique em um ponto no mapa para selecionar.")

    # Usar o st.plotly_chart com on_select para detectar cliques
    event = st.plotly_chart(fig, use_container_width=True, on_select="rerun")

    # Verificar se o evento de seleção tem pontos válidos
    if event and "points" in event.selection and event.selection["points"]:
        # Pegar o primeiro ponto selecionado e checar as coordenadas
        point = event.selection["points"][0]
        click_coords = (point.get("lat"), point.get("lon"))  # latitude e longitude
        if click_coords[0] is not None and click_coords[1] is not None:
            click_data = click_coords
            st.session_state.click_data = click_data
        else:
            st.warning("Seleção inválida. Tente selecionar um ponto válido no mapa.")
    else:
        st.warning("Nenhum ponto foi selecionado.")

else:
    st.plotly_chart(fig, use_container_width=True)

# Se houver dados de clique, filtrar pontos dentro do raio e exibir o novo mapa
if click_data:
    pontos_no_raio = {}
    
    # Verificar a distância de cada ponto em relação ao ponto clicado
    for file_name, df in company_data.items():
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
        st.plotly_chart(fig_filtrado, use_container_width=True)
        st.write(f"Pontos encontrados dentro de {raio_selecao} km do ponto clicado:")
    else:
        st.write(f"Nenhum ponto encontrado dentro de {raio_selecao} km do ponto clicado.")