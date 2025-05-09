import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import folium_static
import plotly.express as px
import matplotlib.pyplot as plt
import numpy as np
import os
from shapely.validation import make_valid

# Set page configuration
st.set_page_config(
    page_title="Solar Suitability Analysis",
    page_icon="☀️",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    body {
        background-color: #0e1117;
        color: white;
    }
    .main-header {
        font-size: 2rem;
        color: white;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: white;
        margin-bottom: 1rem;
    }
    /* Hide development info */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Force columns to display correctly */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
    }
    
    /* Keep the map column from collapsing */
    [data-testid="column"]:nth-of-type(2) {
        min-width: 65% !important;
    }
    
    /* Make sure controls column isn't too wide */
    [data-testid="column"]:nth-of-type(1) {
        max-width: 35% !important;
    }
</style>
""", unsafe_allow_html=True)

# Main title - moved outside the columns
st.title("Solar Suitability Analysis")
st.write("Explore solar suitability across different states and districts in India")

# Try to find and load the shapefile
def find_shapefile(base_name):
    """Try to find the shapefile in various locations"""
    # Check current directory
    if os.path.exists(f"{base_name}.shp"):
        return f"{base_name}.shp"
    
    # Check parent directory
    parent_dir = os.path.dirname(os.getcwd())
    if os.path.exists(os.path.join(parent_dir, f"{base_name}.shp")):
        return os.path.join(parent_dir, f"{base_name}.shp")
    
    # Look for any .shp file in current directory
    for file in os.listdir('.'):
        if file.endswith('.shp'):
            return file
    
    # Return the original name if nothing found
    return f"{base_name}.shp"

# Try to load the shapefile
shapefile_path = find_shapefile("Solar_Suitability_layer")

try:
    # Basic loading attempt
    gdf = gpd.read_file(shapefile_path)
    st.success(f"Successfully loaded shapefile with {len(gdf)} features")
    
    # Define category names
    categories = {
        "Adaptation": "Adaptation",
        "Mitigation": "Mitigation", 
        "Replacment": "Replacement",  # Original column name in data (has spelling error)
        "General_SI": "General SI"
    }
    
    # Create a two-column layout for controls and map
    # Using specific column widths to ensure proper display
    cols = st.columns([1, 2])
    
    # Controls column
    with cols[0]:
        st.header("Selection Controls")
        
        # State selection
        st.subheader("Select State:")
        states = ["All States"]
        if "NAME_1" in gdf.columns:
            valid_states = [str(s) for s in gdf["NAME_1"].unique() if s is not None and str(s) != "nan"]
            states.extend(sorted(valid_states))
        
        selected_state = st.selectbox("", states, label_visibility="collapsed")
        
        # Filter by state
        if selected_state != "All States":
            filtered_gdf = gdf[gdf["NAME_1"] == selected_state]
        else:
            filtered_gdf = gdf
        
        # District selection
        st.subheader("Select District:")
        districts = ["All Districts"]
        if "NAME_2" in gdf.columns:
            if selected_state != "All States":
                valid_districts = [str(d) for d in filtered_gdf["NAME_2"].unique() if d is not None and str(d) != "nan"]
            else:
                valid_districts = [str(d) for d in gdf["NAME_2"].unique() if d is not None and str(d) != "nan"]
            districts.extend(sorted(valid_districts))
        
        selected_district = st.selectbox("", districts, label_visibility="collapsed")
        
        # Filter by district
        if selected_district != "All Districts":
            filtered_gdf = filtered_gdf[filtered_gdf["NAME_2"] == selected_district]
        
        # Category selection
        st.subheader("Select Category:")
        selected_category = st.selectbox(
            "",
            list(categories.keys()),
            format_func=lambda x: categories[x],
            label_visibility="collapsed"
        )
        
        # Legend section
        st.header("Legend")
        
        # Get unique values for the selected category
        if selected_category in filtered_gdf.columns:
            unique_values = [v for v in filtered_gdf[selected_category].unique() if v is not None and str(v) != "nan"]
            
            for value in unique_values:
                if "Highly Suitable" in str(value):
                    color = "#4dff4d"  # Green
                elif "Moderately Suitable" in str(value):
                    color = "#ffeb3b"  # Yellow
                else:
                    color = "#808080"  # Gray
                    
                st.markdown(
                    f"<div style='display: flex; align-items: center; margin-bottom: 5px;'><div style='width: 15px; height: 15px; background-color: {color}; margin-right: 10px;'></div><div>{value}</div></div>",
                    unsafe_allow_html=True
                )
    
    # Map column
    with cols[1]:
        st.header("Solar Suitability Map")
        
        # Create a basic map
        if not filtered_gdf.empty:
            # Get the center coordinates
            try:
                center_y = filtered_gdf.geometry.centroid.y.mean()
                center_x = filtered_gdf.geometry.centroid.x.mean()
                center = [center_y, center_x]
            except:
                # Default to center of India if calculation fails
                center = [20.5937, 78.9629]
            
            # Calculate zoom level based on extent
            bounds = filtered_gdf.geometry.total_bounds
            lat_diff = bounds[3] - bounds[1]
            lon_diff = bounds[2] - bounds[0]
            zoom_level = 7
            if lat_diff > 3 or lon_diff > 3:
                zoom_level = 6
            elif lat_diff < 1 or lon_diff < 1:
                zoom_level = 9
            
            m = folium.Map(location=center, zoom_start=zoom_level, tiles="CartoDB positron")
            
            # Style function based on selected category
            def style_function(feature):
                if selected_category in feature['properties'] and feature['properties'][selected_category] is not None:
                    category_value = str(feature['properties'][selected_category])
                    
                    # Choose color based on suitability level
                    if "Highly Suitable" in category_value:
                        return {'fillColor': '#4dff4d', 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
                    elif "Moderately Suitable" in category_value:
                        return {'fillColor': '#ffeb3b', 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
                    else:
                        return {'fillColor': '#808080', 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
                else:
                    return {'fillColor': '#808080', 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
            
            # Add GeoJSON layer with tooltips
            folium.GeoJson(
                filtered_gdf,
                style_function=style_function,
                tooltip=folium.GeoJsonTooltip(
                    fields=["NAME_2", selected_category] if "NAME_2" in filtered_gdf.columns else ["OBJECTID", selected_category],
                    aliases=["District", categories[selected_category]] if "NAME_2" in filtered_gdf.columns else ["ID", categories[selected_category]],
                    localize=True
                )
            ).add_to(m)
            
            # Display the map - set width and height explicitly
            folium_static(m, width=800, height=600)
            
            # Display district details if a specific district is selected
            if selected_district != "All Districts":
                st.subheader(f"Details for {selected_district}")
                district_data = filtered_gdf.iloc[0]
                
                # Display each category value
                for category, display_name in categories.items():
                    if category in district_data:
                        value = district_data[category]
                        if value is not None and str(value) != "nan":
                            st.write(f"**{display_name}:** {value}")
        else:
            st.warning("No data available for the selected filters.")

except Exception as e:
    st.error(f"Error: {e}")
    
    # Debugging information
    st.subheader("Troubleshooting Information")
    st.write(f"Current working directory: {os.getcwd()}")
    st.write("Files in current directory:")
    st.write(os.listdir('.'))
    
    # Check for specific shapefile components
    components = [".shp", ".dbf", ".shx", ".prj"]
    found_components = []
    missing_components = []
    
    for comp in components:
        if os.path.exists(f"Solar_Suitability_layer{comp}"):
            found_components.append(f"Solar_Suitability_layer{comp}")
        else:
            missing_components.append(f"Solar_Suitability_layer{comp}")
    
    if found_components:
        st.write("Found shapefile components:")
        st.write(found_components)
    
    if missing_components:
        st.warning("Missing shapefile components:")
        st.write(missing_components)