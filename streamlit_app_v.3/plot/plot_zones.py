import plotly.express as px
import matplotlib.colors as mcolors

# Constants
MAPBOX_USERNAME = "projetodados"
MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoicHJvamV0b2RhZG9zIiwiYSI6ImNtMXdiOTEydDA1czEyaW41MDYwamIwdGQifQ.CntGc8JTYWf6b9tveFDAVQ"

# Set the Mapbox access token globally
px.set_mapbox_access_token(MAPBOX_ACCESS_TOKEN)

# Functions
def plot_zones_with_colors(gdf, width=1800, height=1200, mapbox_style="carto-positron", color_var="zl_zona", hover_data=["zl_zona"]):

    # Ensure CRS is WGS84
    gdf = gdf.to_crs(epsg=4326)

    # Handle custom Mapbox styles
    if mapbox_style == "satellite-streets":
        mapbox_style = "mapbox://styles/mapbox/satellite-streets-v12"
    if mapbox_style == "satellite":
        mapbox_style = "mapbox://styles/mapbox/satellite-v9"
    
    # Plot the data
    fig = px.choropleth_mapbox(gdf,
                                geojson=gdf.geometry,
                                locations=gdf.index,
                                color=color_var,
                                color_discrete_sequence=list(mcolors.TABLEAU_COLORS.values()),
                                mapbox_style=mapbox_style,
                                zoom=11, 
                                center={"lat": -23.55028, "lon": -46.63389},
                                opacity=0.5,
                                labels={color_var:color_var},
                                hover_data=hover_data
                               )
    
    fig.update_geos(fitbounds="locations", visible=False)

    # Increase map size
    fig.update_layout(
        width=width,  
        height=height,
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    # Save the plot
    return fig