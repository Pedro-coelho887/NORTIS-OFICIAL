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


def encontrar_arquivo(nome_arquivo, pasta_inicial=None):
       if pasta_inicial is None:
        pasta_inicial = os.getcwd()
        for raiz, pastas, arquivos in os.walk(pasta_inicial):
            if nome_arquivo in arquivos:
                return os.path.join(raiz, nome_arquivo)
        return None
       
# Função para associar os pontos a seus distritos
def assign_districts_to_points(points_gdf, districts_gdf):
    points_gdf = points_gdf.set_geometry(gpd.points_from_xy(points_gdf['Longitude'], points_gdf['Latitude']))
    points_gdf = points_gdf.set_crs(districts_gdf.crs, allow_override=True)

    # Fazer o spatial join para associar pontos aos distritos
    points_with_districts = gpd.sjoin(points_gdf, districts_gdf[['geometry', 'NOME_DIST']], how="left", predicate="within")
    return points_with_districts

def convert_km_to_degree(km):
    return km / 111.0

# Função de distância personalizada
def custom_great_circle(u, v):
    # u e v são vetores contendo [latitude, longitude]
    return great_circle(u, v).km

# Slider global para a distância de agrupamento
distancia_agrupamento = st.slider(
    'Distância para agrupar (em km)', 
    min_value=0.0, 
    max_value=50.0, 
    step=1.0, 
    value=5.0
)

from pyproj import Transformer

# Função para converter coordenadas geográficas para UTM
def latlon_to_utm(df, zone=23):
    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:327{zone}", always_xy=True)  # Projeção UTM zona 23S
    df['UTM_East'], df['UTM_North'] = transformer.transform(df['Longitude'].values, df['Latitude'].values)
    return df

# Converter km para metros diretamente
def convert_km_to_meters(km):
    return km * 100

def cluster_points(df, distancia_km):
    if df.empty:
        return df

    # Converter coordenadas geográficas para UTM
    df = latlon_to_utm(df)

    # Usar as coordenadas UTM (em metros) para a lógica de agrupamento
    coordinates = df[['UTM_East', 'UTM_North']].to_numpy()
    
    # Inicializar uma lista para armazenar os clusters
    clusters = [-1] * len(df)  # -1 significa que o ponto ainda não foi agrupado
    cluster_id = 0

    # Definir a distância máxima para agrupar em metros
    distancia_metros = convert_km_to_meters(distancia_km)

    # Enquanto houver pontos não agrupados
    for i in range(len(df)):
        if clusters[i] == -1:  # Ponto ainda não foi agrupado
            # Começa um novo cluster com o ponto i
            clusters[i] = cluster_id
            grupo_pendentes = [i]  # Iniciar com o ponto atual
            
            # Iterar sobre pontos pendentes para encontrar próximos
            while grupo_pendentes:
                ponto_atual = grupo_pendentes.pop(0)
                for j in range(len(df)):
                    if clusters[j] == -1:  # Verificar apenas os pontos ainda não agrupados
                        # Calcular a distância entre o ponto atual e o ponto j
                        dist = np.linalg.norm(coordinates[ponto_atual] - coordinates[j])
                        if dist <= distancia_metros:  # Se estiver dentro da distância, agrupar
                            clusters[j] = cluster_id
                            grupo_pendentes.append(j)
            
            # Incrementar o ID do cluster para o próximo grupo
            cluster_id += 1

    # Adicionar o rótulo do cluster ao DataFrame original
    df['Cluster'] = clusters

    # Agrupar os pontos por cluster, mantendo o nome do Transporte e a contagem de pontos
    clustered_data = df.groupby(['Cluster', 'Transporte']).agg({
        'Latitude': 'mean',
        'Longitude': 'mean',
        'Cluster': 'size'
    }).rename(columns={'Cluster': 'Num_Points'}).reset_index()

    return clustered_data

# Função para limpar e formatar CEPs
def clean_and_format_cep(cep):
    if pd.notnull(cep):
        cep_str = str(cep).strip().replace('-', '').replace('.', '').replace('[', '').replace(']', '').split(',')[0]
        try:
            return int(cep_str)
        except ValueError:
            return None
    return None

# Função para carregar e preparar dados das planilhas
def load_and_prepare_excel_data(file_path):
    df = pd.read_excel(file_path)
    # Verifica se as colunas de coordenadas estão presentes
    if 'longitude' in df.columns and 'latitude' in df.columns:
        # Normaliza as colunas para manter o padrão
        df.rename(columns={'longitude': 'Longitude', 'latitude': 'Latitude'}, inplace=True)
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        
        # Verifica se há dados vazios de longitude e latitude e os remove
        df = df.dropna(subset=['Longitude', 'Latitude'])
    
    elif 'CEP' in df.columns:
        df['CEP'] = df['CEP'].apply(clean_and_format_cep)
    
    else:
        st.warning(f"O arquivo {file_path} não contém CEP ou coordenadas (Longitude e Latitude).")
    return df

# Carregar todas as planilhas na pasta 'data/companies'
def load_all_companies_data(folder_path):
    folder = Path(folder_path)
    return {file.stem: load_and_prepare_excel_data(file) for file in folder.glob("*.xlsx")}

# Função para carregar o arquivo GeoJSON
def load_geojson(file_path):
    return gpd.read_file(file_path)

# Função para buscar coordenadas com base no CEP
def get_coordinates_by_cep(df, bairros_df):
    df_with_coords = pd.merge(df, bairros_df, on='CEP', how='left')
    df_with_coords = df_with_coords.dropna(subset=['Latitude', 'Longitude'])
    return df_with_coords

# Função para filtrar dados dentro do contorno
def filter_lat_lon_within_contour_using_cep(df, file_name, bairros_df, contour_gdf):
    if 'CEP' in df.columns:
        df_with_coords = get_coordinates_by_cep(df, bairros_df)
        if df_with_coords.empty:
            st.warning(f"Não foi possível encontrar coordenadas para os CEPs no arquivo {file_name}")
            return pd.DataFrame()
        gdf = gpd.GeoDataFrame(df_with_coords, geometry=gpd.points_from_xy(df_with_coords['Longitude'], df_with_coords['Latitude']))
        points_within = gdf[gdf.within(contour_gdf.union_all())]
        #points_outside = len(gdf) - len(points_within)
        #if points_outside > 0:
            #st.warning(f"{points_outside} pontos do arquivo {file_name} estão fora do contorno e não serão plotados.")
        
        # Adicionar coluna 'Transporte' com o nome do arquivo
        points_within['Transporte'] = file_name
        
        return points_within[['CEP', 'Latitude', 'Longitude', 'Transporte']]
    else:
        st.warning(f"Coluna CEP não encontrada no arquivo {file_name}")
        return pd.DataFrame()

# Função para filtrar dados dentro do contorno usando latitude e longitude diretamente
def filter_lat_lon_within_contour(df, file_name, contour_gdf):
    if 'Longitude' in df.columns and 'Latitude' in df.columns:
        gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['Longitude'], df['Latitude']))
        points_within = gdf[gdf.within(contour_gdf.union_all())]
        
        if points_within.empty:
            st.warning(f"Todos os pontos do arquivo {file_name} estão fora do contorno e não serão plotados.")
            return pd.DataFrame()
        
        points_within['Transporte'] = file_name
        
        return points_within[['Latitude', 'Longitude', 'Transporte']]
    else:
        st.warning(f"Colunas Longitude/Latitude não encontradas no arquivo {file_name}.")
        return pd.DataFrame()

# Exemplo de função combinada para CEP ou Latitude/Longitude
def filter_data_within_contour(df, file_name, bairros_df, contour_gdf):
    if 'CEP' in df.columns:
        return filter_lat_lon_within_contour_using_cep(df, file_name, bairros_df, contour_gdf)
    elif 'Longitude' in df.columns and 'Latitude' in df.columns:
        return filter_lat_lon_within_contour(df, file_name, contour_gdf)
    else:
        st.warning(f"O arquivo {file_name} não contém dados válidos de CEP ou coordenadas.")
        return pd.DataFrame()

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
                    lambda row: f"Cluster de {row['Num_Points']} pontos<br>Transporte: {row['Transporte']}<br>Distrito: {row['NOME_DIST']}", axis=1
                )
            else:
                clustered_gdf['Num_Points'] = 1
                clustered_gdf['hover_text'] = clustered_gdf.apply(
                    lambda row: f"Ponto único<br>Transporte: {row['Transporte']}<br>Distrito: {row['NOME_DIST']}", axis=1
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
                text=clustered_gdf['Num_Points'].astype(str),  # Mostra o número de Transportes agrupados
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
        title="Pontos Agrupados de Transportes e Distritos em São Paulo",
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
company_data = load_all_companies_data('data/shapefiles/transporte/output_xlsx_files/')
bairros_df = load_and_prepare_excel_data(encontrar_arquivo('bairros.xlsx'))

# Sidebar para escolher os arquivos e distritos
selected_files = st.sidebar.multiselect("Escolha os arquivos para plotar", list(company_data.keys()))
#selected_districts = st.sidebar.multiselect("Escolha os distritos para plotar", districts_gdf['NOME_DIST'].unique().tolist(), default=districts_gdf['NOME_DIST'].unique().tolist())
selected_districts = districts_gdf['NOME_DIST'].unique().tolist()

# Definir cores para os pontos de empresas
color_dict = {
    'Estacao de Metro':'red',
    'Projetos de Estacao de Metro':'blue',
    'Estacao de Trem':'green',
    'Projetos de Estacao de Trem':'black',
    'Ponto de onibus':'brown',
    'Terminal de onibus':'orange',
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