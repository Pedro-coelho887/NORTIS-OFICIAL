# external imports
from pathlib import Path
import streamlit as st
import geopandas as gpd
import pandas as pd
pd.set_option('display.max_columns', None)
gdf =gpd.read_file ('\\Documentos\\GitHub\\NORTIS-OFICIAL\\streamlit_app_v.3\\data\\dados_gerais\\distritos.geojson')
print(gdf.columns)
