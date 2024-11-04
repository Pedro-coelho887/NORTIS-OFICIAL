# External imports
from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
from geopy.distance import great_circle
import streamlit as st

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

from pyproj import Transformer

# Função para converter coordenadas geográficas para UTM
def latlon_to_utm(df, zone=23):
    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:327{zone}", always_xy=True)  # Projeção UTM zona 23S
    df['UTM_East'], df['UTM_North'] = transformer.transform(df['Longitude'].values, df['Latitude'].values)
    return df

# Converter km para metros diretamente
def convert_km_to_meters(km):
    return km * 1000

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

    # Agrupar os pontos por cluster, mantendo o nome do estabelecimento e a contagem de pontos
    clustered_data = df.groupby(['Cluster', 'Estabelecimento']).agg({
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
@st.cache_data
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
@st.cache_data
def load_all_companies_data(folder_path):
    folder = Path(folder_path)
    return {file.stem: load_and_prepare_excel_data(file) for file in folder.glob("*.xlsx")}

# Função para carregar o arquivo GeoJSON
@st.cache_data
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
        
        # Adicionar coluna 'Estabelecimento' com o nome do arquivo
        points_within['Estabelecimento'] = file_name
        
        return points_within[['CEP', 'Latitude', 'Longitude', 'Estabelecimento']]
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
        
        points_within['Estabelecimento'] = file_name
        
        return points_within[['Latitude', 'Longitude', 'Estabelecimento']]
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