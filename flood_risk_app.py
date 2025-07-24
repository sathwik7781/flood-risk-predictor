import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium import plugins
import io
import base64
from streamlit_folium import st_folium

# Configure page
st.set_page_config(
    page_title="🌊 Flood Risk Predictor",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def generate_sample_data():
    """Generate sample data for testing"""
    np.random.seed(42)
    n_points = 50
    
    # Generate coordinates around a fictional area
    base_lat, base_lon = 40.7128, -74.0060  # NYC area
    
    data = {
        'Latitude': np.random.normal(base_lat, 0.1, n_points),
        'Longitude': np.random.normal(base_lon, 0.1, n_points),
        'Elevation': np.random.uniform(0, 50, n_points),
        'Rainfall': np.random.uniform(10, 100, n_points)
    }
    
    df = pd.DataFrame(data)
    df = df.round(6)
    return df

def calculate_flood_risk(elevation, rainfall):
    """Calculate flood risk based on elevation and rainfall"""
    if elevation < 10 and rainfall > 50:
        return "High"
    elif elevation < 20 and rainfall > 30:
        return "Medium"
    else:
        return "Low"

def get_risk_color(risk):
    """Get color for risk level"""
    colors = {
        "High": "red",
        "Medium": "orange", 
        "Low": "green"
    }
    return colors.get(risk, "gray")

def create_flood_map(df):
    """Create interactive folium map with flood risk visualization"""
    if df.empty:
        return None
    
    # Calculate map center
    center_lat = df['Latitude'].mean()
    center_lon = df['Longitude'].mean()
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles='OpenStreetMap'
    )
    
    # Add markers for each point
    for idx, row in df.iterrows():
        color = get_risk_color(row['Flood_Risk'])
        
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=8,
            popup=f"""
            <b>Point {idx + 1}</b><br>
            Lat: {row['Latitude']:.4f}<br>
            Lon: {row['Longitude']:.4f}<br>
            Elevation: {row['Elevation']:.1f}m<br>
            Rainfall: {row['Rainfall']:.1f}mm<br>
            <b>Risk: {row['Flood_Risk']}</b>
            """,
            color='black',
            weight=1,
            fillColor=color,
            fillOpacity=0.7
        ).add_to(m)
    
    # Add legend
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 150px; height: 90px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p><b>Flood Risk Legend</b></p>
    <p><i class="fa fa-circle" style="color:red"></i> High Risk</p>
    <p><i class="fa fa-circle" style="color:orange"></i> Medium Risk</p>
    <p><i class="fa fa-circle" style="color:green"></i> Low Risk</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def download_csv(df, filename):
    """Create download link for CSV"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 Download Results CSV</a>'
    return href

def main():
    # Header
    st.title("🌊 Flood Risk Predictor MVP")
    st.markdown("Predict flood-prone zones based on elevation and rainfall data")
    
    # Sidebar
    st.sidebar.header("📊 Data Input")
    
    # Option to use sample data or upload
    data_option = st.sidebar.radio(
        "Choose data source:",
        ["Use Sample Data", "Upload CSV File"]
    )
    
    df = pd.DataFrame()
    
    if data_option == "Use Sample Data":
        st.sidebar.success("Using generated sample data")
        df = generate_sample_data()
        
        # Show sample data download
        sample_csv = df.to_csv(index=False)
        st.sidebar.download_button(
            label="📥 Download Sample Data",
            data=sample_csv,
            file_name="sample_flood_data.csv",
            mime="text/csv"
        )
        
    else:
        uploaded_file = st.sidebar.file_uploader(
            "Upload CSV file",
            type=['csv'],
            help="CSV should contain columns: Latitude, Longitude, Elevation, Rainfall"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
            except Exception as e:
                st.sidebar.error(f"Error reading file: {e}")
                return
    
    # Validate data
    if not df.empty:
        required_cols = ['Latitude', 'Longitude', 'Elevation', 'Rainfall']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"Missing required columns: {', '.join(missing_cols)}")
            st.info("Required columns: Latitude, Longitude, Elevation, Rainfall")
            return
        
        # Calculate flood risk
        df['Flood_Risk'] = df.apply(
            lambda row: calculate_flood_risk(row['Elevation'], row['Rainfall']), 
            axis=1
        )
        
        # Main content area
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📋 Risk Assessment Results")
            
            # Risk summary
            risk_counts = df['Flood_Risk'].value_counts()
            
            # Display metrics
            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            
            with metrics_col1:
                st.metric(
                    "🔴 High Risk", 
                    risk_counts.get('High', 0),
                    help="Elevation < 10m AND Rainfall > 50mm"
                )
            
            with metrics_col2:
                st.metric(
                    "🟡 Medium Risk", 
                    risk_counts.get('Medium', 0),
                    help="Elevation < 20m AND Rainfall > 30mm"
                )
            
            with metrics_col3:
                st.metric(
                    "🟢 Low Risk", 
                    risk_counts.get('Low', 0),
                    help="All other conditions"
                )
            
            # Show data table
            st.subheader("📊 Detailed Results")
            
            # Add filters
            risk_filter = st.multiselect(
                "Filter by risk level:",
                options=['High', 'Medium', 'Low'],
                default=['High', 'Medium', 'Low']
            )
            
            filtered_df = df[df['Flood_Risk'].isin(risk_filter)]
            
            st.dataframe(
                filtered_df.round(4),
                use_container_width=True,
                height=300
            )
            
            # Download button
            if not filtered_df.empty:
                csv_data = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Results CSV",
                    data=csv_data,
                    file_name="flood_risk_results.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col2:
            st.subheader("🗺️ Interactive Risk Map")
            
            # Create and display map
            flood_map = create_flood_map(df)
            
            if flood_map:
                st_folium(flood_map, width=700, height=500)
            else:
                st.error("Unable to create map")
        
        # Additional analysis
        st.subheader("📈 Risk Analysis")
        
        analysis_col1, analysis_col2 = st.columns(2)
        
        with analysis_col1:
            st.write("**Risk Distribution:**")
            risk_percentages = (risk_counts / len(df) * 100).round(1)
            for risk, count in risk_counts.items():
                percentage = risk_percentages[risk]
                st.write(f"• {risk} Risk: {count} points ({percentage}%)")
        
        with analysis_col2:
            st.write("**Data Summary:**")
            st.write(f"• Total Points: {len(df)}")
            st.write(f"• Avg Elevation: {df['Elevation'].mean():.1f}m")
            st.write(f"• Avg Rainfall: {df['Rainfall'].mean():.1f}mm")
            st.write(f"• High Risk Areas: {(risk_counts.get('High', 0) / len(df) * 100):.1f}%")
    
    else:
        # Show instructions when no data
        st.info("👆 Please select a data source from the sidebar to begin analysis")
        
        st.subheader("📖 How to Use")
        st.markdown("""
        1. **Choose Data Source**: Use sample data or upload your own CSV
        2. **CSV Format**: Ensure your file has columns: `Latitude`, `Longitude`, `Elevation`, `Rainfall`
        3. **View Results**: See risk assessment table and interactive map
        4. **Download**: Export results as CSV file
        
        **Risk Calculation Rules:**
        - 🔴 **High Risk**: Elevation < 10m AND Rainfall > 50mm
        - 🟡 **Medium Risk**: Elevation < 20m AND Rainfall > 30mm  
        - 🟢 **Low Risk**: All other conditions
        """)
        
        # Sample data preview
        st.subheader("📋 Sample Data Format")
        sample_preview = pd.DataFrame({
            'Latitude': [40.7128, 40.7589, 40.6892],
            'Longitude': [-74.0060, -73.9851, -74.0445],
            'Elevation': [5.2, 15.8, 25.1],
            'Rainfall': [65.3, 45.7, 25.9]
        })
        st.dataframe(sample_preview, use_container_width=True)

if __name__ == "__main__":
    main()