import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import folium_static
import os
import matplotlib.pyplot as plt
import numpy as np

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
    .statistics-section {
        margin-top: 2rem;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #1E1E1E;
    }
    .guide-button {
        background-color: #1E1E1E;
        color: white;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        text-align: center;
        border: none;
        cursor: pointer;
    }
    /* Color gradient for legend - exactly matching screenshot */
    .legend-gradient {
        width: 100%;
        height: 20px;
        border-radius: 4px;
        margin-bottom: 5px;
        background: linear-gradient(to right, #FF0000, #FFA500, #FFFF00, #90EE90, #00FF00);
    }
    .legend-labels {
        display: flex;
        justify-content: space-between;
        font-size: 0.8rem;
    }
    /* Hide development info */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* Button styling */
    .stButton>button {
        background-color: #1E1E1E;
        color: white;
        border: 1px solid #333;
    }
    /* Smooth scrolling for anchor links */
    html {
        scroll-behavior: smooth;
    }
</style>
""", unsafe_allow_html=True)

# Use cache to speed up shapefile loading
@st.cache_data
def load_shapefile(file_path):
    """Load the shapefile and cache the result for better performance"""
    try:
        return gpd.read_file(file_path)
    except Exception as e:
        st.error(f"Error loading shapefile: {e}")
        return None

# Define a single consistent color mapping for all categories
# Match exactly the colors from the screenshot
color_mapping = {
    "Less Suitable": "#FF0000",  # Red
    "Moderately Suitable": "#BBBBBB",  # Light gray (as shown in screenshot)
    # All "Highly Suitable" variations will be bright green (#00FF00)
    "Highly Suitable (Adaptation )": "#00FF00",
    "Highly Suitable (Adaptation + Mitigation + On Grid": "#00FF00",
    "Highly Suitable (Adaptation + Mitigation)": "#00FF00",
    "Highly Suitable (Adaptation + On Grid Community We": "#00FF00",
    "Highly Suitable (Adaptation + On Grid Replacement)": "#00FF00",
    "Highly Suitable (Mitigation + On Grid Community We": "#00FF00",
    "Highly Suitable (Mitigation + On Grid Replacement)": "#00FF00",
    "Highly Suitable (Mitigation)": "#00FF00",
    "Highly Suitable (On Grid Community Wells)": "#00FF00",
    "Highly Suitable (On Grid Replacement)": "#00FF00",
    "Highly Suitable": "#00FF00"
}

# Function to calculate statistics
def calculate_statistics(gdf, category):
    """Calculate statistics for the selected category"""
    if category not in gdf.columns:
        return None
    
    stats = {}
    # Count occurrences of each suitability level
    if gdf[category].dtype == 'object':
        value_counts = gdf[category].value_counts()
        total = len(gdf)
        
        stats['counts'] = {}
        for value, count in value_counts.items():
            if value is not None and str(value) != "nan":
                percentage = (count / total) * 100
                stats['counts'][value] = {
                    'count': int(count),
                    'percentage': round(percentage, 2)
                }
    
    return stats

# Try to find the shapefile
shapefile_path = "Solar_Suitability_layer.shp"
for file in os.listdir('.'):
    if file.endswith('.shp'):
        shapefile_path = file
        break

# Define category names
categories = {
    "Adaptation": "Adaptation",
    "Mitigation": "Mitigation", 
    "Replacment": "Replacement",  # Original column name in data (has spelling error)
    "General_SI": "General SI"
}

# Load the shapefile
gdf = load_shapefile(shapefile_path)

if gdf is not None:
    # Main title
    st.title("Solar Suitability Analysis")
    st.write("Explore solar suitability across different states and districts in India")
    
    # Create a two-column layout for controls and map
    controls_col, map_col = st.columns([1, 2])
    
    with controls_col:
        # Selection controls section
        st.header("Selection Controls")
        
        # State selection
        st.subheader("Select State:")
        states = ["All States"]
        if "NAME_1" in gdf.columns:
            valid_states = [str(s) for s in gdf["NAME_1"].unique() if s is not None and str(s) != "nan"]
            states.extend(sorted(valid_states))
        
        selected_state = st.selectbox("State", states, label_visibility="collapsed")
        
        # District selection
        st.subheader("Select District:")
        
        # Filter geodataframe by state for district dropdown
        if selected_state != "All States":
            state_filtered = gdf[gdf["NAME_1"] == selected_state]
        else:
            state_filtered = gdf
            
        districts = ["All Districts"]
        if "NAME_2" in gdf.columns:
            valid_districts = [str(d) for d in state_filtered["NAME_2"].unique() if d is not None and str(d) != "nan"]
            districts.extend(sorted(valid_districts))
        
        selected_district = st.selectbox("District", districts, label_visibility="collapsed")
        
        # Category selection
        st.subheader("Select Category:")
        selected_category = st.selectbox(
            "Category",
            list(categories.keys()),
            format_func=lambda x: categories[x],
            label_visibility="collapsed"
        )
        
        # Apply all filters directly without caching
        if selected_state != "All States":
            filtered_gdf = gdf[gdf["NAME_1"] == selected_state]
        else:
            filtered_gdf = gdf
            
        if selected_district != "All Districts":
            filtered_gdf = filtered_gdf[filtered_gdf["NAME_2"] == selected_district]
        
        # Legend section with simplified colors
        st.header("Legend")
        
        # Create gradient legend
        st.markdown('<div class="legend-gradient"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="legend-labels"><span>Less Suitable</span><span>Moderately Suitable</span><span>Highly Suitable</span></div>',
            unsafe_allow_html=True
        )
        
        # Get unique values for the selected category
        if selected_category in filtered_gdf.columns:
            unique_values = [v for v in filtered_gdf[selected_category].unique() if v is not None and str(v) != "nan"]
            st.subheader("Suitability Levels")
            
            # Group by color category
            green_values = []
            gray_values = []
            red_values = []
            other_values = []
            
            for value in unique_values:
                if value is not None and str(value) != "nan":
                    if "Highly Suitable" in str(value):
                        green_values.append(value)
                    elif "Moderately Suitable" in str(value):
                        gray_values.append(value)
                    elif "Less Suitable" in str(value):
                        red_values.append(value)
                    else:
                        other_values.append(value)
            
            # Display red values first
            for value in sorted(red_values):
                st.markdown(
                    f"<div style='display: flex; align-items: center; margin-bottom: 5px;'><div style='width: 15px; height: 15px; background-color: #FF0000; margin-right: 10px;'></div><div>{value}</div></div>",
                    unsafe_allow_html=True
                )
            
            # Display gray values next
            for value in sorted(gray_values):
                st.markdown(
                    f"<div style='display: flex; align-items: center; margin-bottom: 5px;'><div style='width: 15px; height: 15px; background-color: #BBBBBB; margin-right: 10px;'></div><div>{value}</div></div>",
                    unsafe_allow_html=True
                )
            
            # Display green values last
            for value in sorted(green_values):
                st.markdown(
                    f"<div style='display: flex; align-items: center; margin-bottom: 5px;'><div style='width: 15px; height: 15px; background-color: #00FF00; margin-right: 10px;'></div><div>{value}</div></div>",
                    unsafe_allow_html=True
                )
            
            # Display any other values
            for value in sorted(other_values):
                st.markdown(
                    f"<div style='display: flex; align-items: center; margin-bottom: 5px;'><div style='width: 15px; height: 15px; background-color: #BBBBBB; margin-right: 10px;'></div><div>{value}</div></div>",
                    unsafe_allow_html=True
                )
    
    # Map column
    with map_col:
        # Create a header row with map title and statistics button side by side
        col1, col2 = st.columns([3, 1])
        with col1:
            st.header("Solar Suitability Map")
        with col2:
            # Add the "View Statistics" button next to the map title
            # This will be a simple anchor link - not a Streamlit button
            st.markdown("""
                <a href="#statistics-section" style="
                    background-color: #1E1E1E;
                    color: white;
                    padding: 8px 16px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 16px;
                    margin: 4px 2px;
                    cursor: pointer;
                    border-radius: 4px;
                    border: 1px solid #333;
                ">View Statistics</a>
            """, unsafe_allow_html=True)
        
        # Create a basic map
        if not filtered_gdf.empty:
            # Calculate map center and zoom based on filtered data
            try:
                bounds = filtered_gdf.geometry.total_bounds
                center_lat = (bounds[1] + bounds[3]) / 2
                center_lon = (bounds[0] + bounds[2]) / 2
                center = [center_lat, center_lon]
                
                # Simple zoom calculation
                zoom_level = 7
                lat_diff = bounds[3] - bounds[1]
                lon_diff = bounds[2] - bounds[0]
                if lat_diff > 3 or lon_diff > 3:
                    zoom_level = 6
                elif lat_diff < 1 or lon_diff < 1:
                    zoom_level = 9
            except:
                # Default center and zoom if calculation fails
                center = [20.5937, 78.9629]
                zoom_level = 5
            
            # Create the map
            m = folium.Map(location=center, zoom_start=zoom_level, tiles="CartoDB positron")
            
            # Simplify geometries for better performance if many features
            if len(filtered_gdf) > 50:
                try:
                    filtered_gdf_simplified = filtered_gdf.copy()
                    filtered_gdf_simplified.geometry = filtered_gdf_simplified.geometry.simplify(0.001)
                except:
                    filtered_gdf_simplified = filtered_gdf
            else:
                filtered_gdf_simplified = filtered_gdf
            
            # Style function matching exactly the screenshot colors
            def style_function(feature):
                if selected_category in feature['properties'] and feature['properties'][selected_category] is not None:
                    category_value = str(feature['properties'][selected_category])
                    
                    # For all "Highly Suitable" categories, use green
                    if "Highly Suitable" in category_value:
                        return {'fillColor': '#00FF00', 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
                    # For "Moderately Suitable", use light gray as in screenshot  
                    elif "Moderately Suitable" in category_value:
                        return {'fillColor': '#BBBBBB', 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
                    # For "Less Suitable", use red
                    elif "Less Suitable" in category_value:
                        return {'fillColor': '#FF0000', 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
                    else:
                        return {'fillColor': '#BBBBBB', 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
                else:
                    return {'fillColor': '#BBBBBB', 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
            
            # Add GeoJSON layer - simplified tooltips approach
            if len(filtered_gdf_simplified) <= 50:
                # For fewer features, include tooltips
                tooltip_fields = ["NAME_2", selected_category] if "NAME_2" in filtered_gdf_simplified.columns else ["OBJECTID", selected_category]
                tooltip_aliases = ["District", categories[selected_category]] if "NAME_2" in filtered_gdf_simplified.columns else ["ID", categories[selected_category]]
                
                # Only include fields that exist in the data
                tooltip_fields = [f for f in tooltip_fields if f in filtered_gdf_simplified.columns]
                tooltip_aliases = tooltip_aliases[:len(tooltip_fields)]
                
                if tooltip_fields:
                    folium.GeoJson(
                        filtered_gdf_simplified,
                        style_function=style_function,
                        tooltip=folium.GeoJsonTooltip(
                            fields=tooltip_fields,
                            aliases=tooltip_aliases,
                            localize=True
                        )
                    ).add_to(m)
                else:
                    folium.GeoJson(
                        filtered_gdf_simplified,
                        style_function=style_function
                    ).add_to(m)
            else:
                # For many features, skip tooltips for better performance
                folium.GeoJson(
                    filtered_gdf_simplified,
                    style_function=style_function
                ).add_to(m)
            
            # Display the map
            folium_static(m, height=500)
            
            # Always show the statistics section below the map
            st.markdown('<div id="statistics-section" class="statistics-section">', unsafe_allow_html=True)
            st.subheader("Statistical Analysis")
            
            # Calculate statistics
            stats = calculate_statistics(filtered_gdf, selected_category)
            
            if stats and 'counts' in stats:
                # Display counts in a table
                st.write(f"**Distribution of {categories[selected_category]} Levels**")
                
                # Prepare data for visualization
                levels = list(stats['counts'].keys())
                counts = [stats['counts'][level]['count'] for level in levels]
                percentages = [stats['counts'][level]['percentage'] for level in levels]
                
                # Create columns for metrics and chart
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # Show key metrics
                    st.write("**Summary:**")
                    total = sum(counts)
                    st.write(f"Total features: {total}")
                    
                    # Table with counts and percentages
                    data = []
                    for level in levels:
                        data.append({
                            "Suitability Level": level,
                            "Count": stats['counts'][level]['count'],
                            "Percentage": f"{stats['counts'][level]['percentage']}%"
                        })
                    
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                
                with col2:
                    # Create a bar chart using matplotlib
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    # Define colors for bars based on suitability level
                    colors = []
                    for level in levels:
                        if "Highly Suitable" in level:
                            colors.append('#00FF00')  # Green for all Highly Suitable
                        elif "Moderately Suitable" in level:
                            colors.append('#BBBBBB')  # Light gray for Moderately Suitable
                        elif "Less Suitable" in level:
                            colors.append('#FF0000')  # Red for Less Suitable
                        else:
                            colors.append('#BBBBBB')  # Light gray for unknown
                    
                    # Create bar chart
                    bars = ax.bar(levels, counts, color=colors)
                    
                    # Add percentage labels on top of bars
                    for i, bar in enumerate(bars):
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                               f'{percentages[i]}%', ha='center', va='bottom',
                               rotation=0, color='white')
                    
                    # Customize chart
                    plt.title(f'Distribution of {categories[selected_category]} Levels')
                    plt.ylabel('Number of Features')
                    plt.xticks(rotation=45, ha='right')
                    
                    # Set dark background for better visibility in dark mode
                    plt.style.use('dark_background')
                    ax.set_facecolor('#1E1E1E')
                    fig.patch.set_facecolor('#1E1E1E')
                    
                    # Display the chart
                    st.pyplot(fig)
                    
                # Add a regional analysis section
                if selected_state != "All States" and "NAME_2" in filtered_gdf.columns:
                    st.subheader(f"Analysis for {selected_state}")
                    
                    # Group by district
                    if selected_district == "All Districts":
                        district_counts = {}
                        for district in filtered_gdf["NAME_2"].unique():
                            if district is not None and str(district) != "nan":
                                district_data = filtered_gdf[filtered_gdf["NAME_2"] == district]
                                if selected_category in district_data.columns:
                                    value = district_data[selected_category].iloc[0] if not district_data.empty else "Unknown"
                                    if value not in district_counts:
                                        district_counts[value] = []
                                    district_counts[value].append(district)
                        
                        # Display districts by suitability level
                        for value, districts in district_counts.items():
                            if value is not None and str(value) != "nan":
                                # Determine color based on value
                                if "Highly Suitable" in str(value):
                                    color = "#00FF00"  # Green
                                elif "Moderately Suitable" in str(value):
                                    color = "#BBBBBB"  # Light gray
                                elif "Less Suitable" in str(value):
                                    color = "#FF0000"  # Red
                                else:
                                    color = "#BBBBBB"  # Light gray
                                
                                st.markdown(
                                    f"<div style='margin-bottom: 10px;'><div style='font-weight: bold; display: flex; align-items: center;'><div style='width: 15px; height: 15px; background-color: {color}; margin-right: 10px;'></div>{value} ({len(districts)} districts)</div></div>",
                                    unsafe_allow_html=True
                                )
                                
                                # List districts in columns for better space utilization
                                cols = st.columns(3)
                                for i, district in enumerate(sorted(districts)):
                                    cols[i % 3].write(f"- {district}")
            else:
                st.warning(f"No statistics available for {categories[selected_category]}. Please check if this category exists in the data.")
            
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("No data available for the selected filters.")
else:
    st.error(f"Could not load shapefile from {shapefile_path}")
    
    # Debugging information
    st.subheader("Troubleshooting Information")
    st.write(f"Current working directory: {os.getcwd()}")
    st.write("Files in current directory:")
    st.write([f for f in os.listdir('.') if f.endswith('.shp') or f.endswith('.dbf') or f.endswith('.shx')])
