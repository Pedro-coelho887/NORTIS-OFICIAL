import plotly.express as px
import matplotlib.colors as mcolors

# Functions
def plot_zones_with_colors(gdf, width=1800, height=1200, mapbox_style="open-street-map", color_var="zl_zona", hover_data=["zl_zona", "areaM2"]):

    # Ensure CRS is WGS84
    gdf = gdf.to_crs(epsg=4326)
    
    # Plot the data
    fig = px.choropleth_mapbox(gdf,
                                geojson=gdf.geometry,
                                locations=gdf.index,
                                color=color_var,
                                color_discrete_sequence=list(mcolors.TABLEAU_COLORS.values()),
                                mapbox_style=mapbox_style,
                                zoom=11, center={"lat": -23.55028, "lon": -46.63389},
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