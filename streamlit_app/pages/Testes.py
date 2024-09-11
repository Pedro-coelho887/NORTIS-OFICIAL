# external imports
from pathlib import Path
import streamlit as st
import geopandas as gpd
import pandas as pd
pd.set_option('display.max_columns', None)
# internal imports
#from plot.plot_zones import plot_zones_with_colors

def load_and_prepare_data(file_path):
    gdf = gpd.read_file(file_path)
    return gdf

def gdf_to_df(gdf):
    gdf['geometry'] = gdf['geometry'].apply(lambda x: x.wkt)
    return gdf

sp_zonas = load_and_prepare_data(Path("C:/Users/pedro/OneDrive/Documentos/GitHub/PROJETO_NORTIS/streamlit_app/data/shapefiles/zoneamento/quadras_z_d.geojson"))
print(sp_zonas['zl_zona'].unique())

lookup_f_op = pd.read_excel(Path('C:/Users/pedro/OneDrive/Documentos/GitHub/PROJETO_NORTIS/streamlit_app/data/lookups/Zonas_fora_de_operacao_urbana.xlsx'))
print(lookup_f_op['Tipo de Zona'].unique())





    #Colunas sp_zonas
#Index(['fid', 'areaM2', 'zl_zona', 'zl_txt_zon', 'zl_tip_lei', 'zl_ano_lei',
#        'zl_num_lei', 'zl_id', 'p_lat', 'p_lon', 'index_right', 'CLASSID',
#        'FEATID', 'REVISIONNU', 'NOME_DIST', 'SIGLA_DIST', 'COD_DIST',
#        'COD_SUB', 'DATA_CRIAC', 'USUARIO_ID', 'geometry'],
#       dtype='object')
    #Colunas lookup_f_op
# Index(['Tipo de Zona', 'Território', 'C.A Máximo', 'Gabarito de Altura Máxima',
#        'Potencial', 'Potencial para projeto imobiliário?']