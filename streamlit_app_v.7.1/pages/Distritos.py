import streamlit as st
import plotly.graph_objects as go
import geopandas as gpd
from Search.Search_Archives import encontrar_arquivo

file_path = encontrar_arquivo('distritos.geojson')
gdf_fronteiras = gpd.read_file(file_path)

# Função para traçar as fronteiras dos distritos
def plot_borders(gdf, width=1800, height=1200, mapbox_style="open-street-map"):
    
    # Garantir que o CRS é WGS84
    gdf = gdf.to_crs(epsg=4326)
    
    # Criar uma lista para armazenar as linhas das fronteiras
    fig = go.Figure()

    # Adiciona as fronteiras de cada distrito
    for _, row in gdf.iterrows():
        geometry = row['geometry']
        if geometry.geom_type == 'Polygon':
            
            lon, lat = geometry.exterior.xy
    
            # Converte para listas
            lon_list = list(lon)
            lat_list = list(lat)


            fig.add_trace(go.Scattermapbox(
                lon=lon_list,
                lat=lat_list,
                mode='lines',
                line=dict(width=2, color='blue'),
                name=row["NOME_DIST"],
                hoverinfo='text',
                hovertext=row["NOME_DIST"]
            ))
        elif geometry.geom_type == 'MultiPolygon':
            for polygon in geometry:
                lon, lat = polygon.exterior.xy
                fig.add_trace(go.Scattermapbox(
                    lon=lon,
                    lat=lat,
                    mode='lines',
                    line=dict(width=2, color='blue'),
                    name=row["NOME_DIST"],
                    hoverinfo='text',
                    hovertext=row["NOME_DIST"]
                ))
    
    # Configurações do layout do mapa
    fig.update_layout(
        mapbox=dict(
            style=mapbox_style,
            center=dict(lat=-23.55028, lon=-46.63389),
            zoom=11
        ),
        width=width,
        height=height,
        margin={"r":0,"t":0,"l":0,"b":0},
        showlegend=False
    )

    return fig

# Interface do Streamlit
mapbox_style = st.selectbox('Estilo do Mapa', ['open-street-map', 'carto-positron', 'carto-darkmatter'])
gdf_fronteiras["geometry"] = gdf_fronteiras["geometry"].simplify(tolerance=10, preserve_topology=True)


# Plotar as fronteiras dos distritos
fig = plot_borders(gdf_fronteiras, mapbox_style=mapbox_style)
st.plotly_chart(fig)
