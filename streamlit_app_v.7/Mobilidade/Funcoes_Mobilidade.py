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
from haversine import haversine, Unit
from pyproj import Transformer

# Função para converter coordenadas geográficas para UTM
def latlon_to_utm(df, zone=23):
    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:327{zone}", always_xy=True)  # Projeção UTM zona 23S
    df['UTM_East'], df['UTM_North'] = transformer.transform(df['Longitude'].values, df['Latitude'].values)
    return df

# Converter km para metros diretamente
def convert_km_to_meters(km):
    return km * 1000

# Função de distância personalizada para DBSCAN usando Haversine
def haversine_distance(latlon1, latlon2):
    return haversine(latlon1, latlon2, unit=Unit.KILOMETERS)

def cluster_points(df, distancia_km):
    if df.empty:
        return df
    
     # Verificar se a distância de agrupamento é 0
    if distancia_km == 0:
        # Não agrupar, apenas retornar os dados originais com uma coluna 'Cluster' preenchida com valores únicos (ou 0)
        df['Cluster'] = range(len(df))
        return df

    # Preparar coordenadas (latitude, longitude) para o DBSCAN
    coordinates = df[['Latitude', 'Longitude']].to_numpy()

    # Aplicar o DBSCAN com Haversine para clustering
    db = DBSCAN(eps=distancia_km, min_samples=1, metric=lambda u, v: haversine(u, v, unit=Unit.KILOMETERS)).fit(coordinates)
    df['Cluster'] = db.labels_

    # Agrupar os pontos por cluster, mantendo o nome do Transporte e a contagem de pontos
    clustered_data = df.groupby('Cluster').agg({
        'Latitude': 'mean',
        'Longitude': 'mean',
        'Cluster': 'size',
        'Transporte': 'first'
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


# Função para filtrar estabelecimentos com base na distância
def filter_mobility_points_by_distance(mobilidade, selection_df, radius_km):
    """
    Filtra os pontos de mobilidade que estão dentro de radius_km de qualquer ponto em selection_df.

    Parameters:
    - mobilidade (dict): Dicionário onde as chaves são os tipos de mobilidade e os valores são DataFrames com colunas 'Latitude' e 'Longitude'.
    - selection_df (pd.DataFrame): DataFrame com colunas 'Latitude' e 'Longitude' dos pontos selecionados.
    - radius_km (float): Raio de filtragem em quilômetros.

    Returns:
    - filtered_mobility (pd.DataFrame): DataFrame combinado com todos os pontos de mobilidade filtrados.
    """
    filtered_mobility_list = []

    for tipo, mobility_df in mobilidade.items():
        if mobility_df is not None and not mobility_df.empty:
            # Converter pontos de mobilidade para GeoDataFrame
            mobility_gdf = gpd.GeoDataFrame(
                mobility_df,
                geometry=gpd.points_from_xy(mobility_df.Longitude, mobility_df.Latitude),
                crs="EPSG:4326"  # Coordenadas geográficas
            )

            # Converter pontos selecionados para GeoDataFrame
            selection_gdf = gpd.GeoDataFrame(
                selection_df,
                geometry=gpd.points_from_xy(selection_df.Longitude, selection_df.Latitude),
                crs="EPSG:4326"
            )

            # Projetar para um CRS métrico (Web Mercator)
            mobility_gdf = mobility_gdf.to_crs(epsg=3857)
            selection_gdf = selection_gdf.to_crs(epsg=3857)

            # Criar buffers ao redor dos pontos selecionados
            selection_gdf['buffer'] = selection_gdf.geometry.buffer(radius_km * 1000)  # Converter km para metros

            # Combinar todos os buffers em uma única geometria
            total_buffer = selection_gdf['buffer'].unary_union

            # Filtrar pontos dentro do buffer
            filtered_gdf = mobility_gdf[mobility_gdf.geometry.within(total_buffer)].copy()

            # Calcular a distância de cada ponto ao ponto selecionado mais próximo
            filtered_gdf['Distancia (m)'] = filtered_gdf.geometry.apply(
                lambda geom: selection_gdf.distance(geom).min()
            ).round(0).astype(int)

            # Adicionar o tipo de mobilidade ao DataFrame filtrado
            filtered_gdf['Tipo'] = tipo

            # Converter de volta para CRS original e armazenar
            filtered_gdf = filtered_gdf.to_crs(epsg=4326)
            filtered_mobility_list.append(filtered_gdf)

    if filtered_mobility_list:
        return pd.concat(filtered_mobility_list).drop(columns='geometry')
    else:
        return pd.DataFrame()
