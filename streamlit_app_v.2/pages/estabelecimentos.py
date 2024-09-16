# External imports
from pathlib import Path
import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import random

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
    if 'CEP' in df.columns:
        df['CEP'] = df['CEP'].apply(clean_and_format_cep)
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
        points_within = gdf[gdf.within(contour_gdf.unary_union)]
        points_outside = len(gdf) - len(points_within)
        if points_outside > 0:
            st.warning(f"{points_outside} pontos do arquivo {file_name} estão fora do contorno e não serão plotados.")
        return points_within[['CEP', 'Latitude', 'Longitude']]
    else:
        st.warning(f"Coluna CEP não encontrada no arquivo {file_name}")
        return pd.DataFrame()

# Função para plotar pontos e distritos
def plot_points_and_districts_with_contour(filtered_data, geojson_gdf, sp_gdf, districts_gdf, color_dict, selected_districts):
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Plotar o contorno de São Paulo
    sp_gdf.plot(ax=ax, color='lightgrey', edgecolor='black', linewidth=1)
    
    # Plotar distritos com cores aleatórias
    if selected_districts:
        districts_to_plot = districts_gdf[districts_gdf['NOME_DIST'].isin(selected_districts)]
    else:
        districts_to_plot = districts_gdf
    
    num_districts = len(districts_to_plot)
    colors = [plt.cm.get_cmap('tab20')(i) for i in range(num_districts)]
    
    for i, (idx, row) in enumerate(districts_to_plot.iterrows()):
        districts_to_plot.iloc[[idx]].plot(ax=ax, color=colors[i], alpha=0.7)
    
    # Plotar pontos dos estabelecimentos
    for file_name, gdf in filtered_data.items():
        if not gdf.empty:
            ax.scatter(gdf['Longitude'], gdf['Latitude'], label=file_name, c=color_dict.get(file_name, 'blue'), alpha=0.6)
    
    plt.title("Pontos de Estabelecimentos e Distritos em São Paulo", fontsize=15)
    plt.legend(title="Estabelecimentos")
    st.pyplot(fig)

# Função para gerar uma tabela dos 10 distritos com mais pontos
def generate_top_districts_table(filtered_data, districts_gdf):
    district_point_count = {district: 0 for district in districts_gdf['NOME_DIST']}
    
    for _, gdf in filtered_data.items():
        for _, point in gdf.iterrows():
            point_geom = gpd.points_from_xy([point['Longitude']], [point['Latitude']])[0]
            for district, geom in zip(districts_gdf['NOME_DIST'], districts_gdf['geometry']):
                if point_geom.within(geom):
                    district_point_count[district] += 1

    sorted_districts = sorted(district_point_count.items(), key=lambda item: item[1], reverse=True)[:10]
    return pd.DataFrame(sorted_districts, columns=['Distrito', 'Número de Pontos'])

# Carregar dados de distritos e contorno de São Paulo
sp_gdf = load_geojson('data/dados_gerais/sao_paulo_contorno.geojson')
districts_gdf = load_geojson('data/dados_gerais/distritos.geojson')

# Carregar os dados das planilhas de empresas e bairros
company_data = load_all_companies_data('data/companies')
bairros_df = load_and_prepare_excel_data('data/dados_gerais/bairros.xlsx')

# Sidebar para escolher os arquivos e distritos
selected_files = st.sidebar.multiselect("Escolha os arquivos para plotar", list(company_data.keys()))
selected_districts = st.sidebar.multiselect("Escolha os distritos para plotar", districts_gdf['NOME_DIST'].unique().tolist(), default=districts_gdf['NOME_DIST'].unique().tolist())

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
}

# Filtrar os dados escolhidos
filtered_data = {file: filter_lat_lon_within_contour_using_cep(company_data[file], file, bairros_df, sp_gdf) for file in selected_files}

# Plotar pontos e distritos
if any(not df.empty for df in filtered_data.values()):
    plot_points_and_districts_with_contour(filtered_data, sp_gdf, sp_gdf, districts_gdf, color_dict, selected_districts)
    
    # Gerar a tabela dos 10 distritos com mais pontos
    top_districts_table = generate_top_districts_table(filtered_data, districts_gdf)
    st.write("Top 10 Distritos com Mais Pontos:")
    st.dataframe(top_districts_table)
else:
    st.warning("Nenhum dado válido encontrado para plotar.")
