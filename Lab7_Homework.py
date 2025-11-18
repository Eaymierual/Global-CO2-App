import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Set Streamlit page configuration
st.set_page_config(
    page_title="Global CO₂ Emissions Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Data Loading and Caching ---
# Use the Our World in Data CO2 dataset, which is publicly accessible via GitHub.
DATA_URL = 'https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv'

@st.cache_data
def load_data():
    """Loads the CO2 emission data from a URL and performs basic cleaning."""
    try:
        # Load the data, using 'country' and 'year' as key columns
        df = pd.read_csv(DATA_URL)
        
        # Filter out aggregated entities like 'World', 'Europe', etc., 
        # but keep 'World' aside for global comparisons if needed.
        # For simplicity in this demo, we will focus on specific countries/entities.
        
        # Ensure 'year' is integer
        df['year'] = df['year'].astype(int)
        
        # Fill NaN values in 'co2' (annual CO2 emissions) with 0 for consistent plotting
        df['co2'] = df['co2'].fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Load the data
data = load_data()

if data.empty:
    st.stop()

# --- Data Preprocessing for Filters and Metrics ---

# Get list of countries (excluding 'World' for the main filter)
country_list = sorted(data['country'].unique())
# Remove 'World' from the standard selection list to focus on specific entities
country_list.remove('World') 
country_list.insert(0, 'United States') # Default selection
country_list.insert(0, 'Global') # Custom "Global" option for aggregation

# Determine the min/max year for the slider
min_year = int(data['year'].min())
max_year = int(data['year'].max())

# --- Sidebar Filters ---
st.sidebar.header("Data Filters")

# Filter 1: Country Selection (Selectbox)
selected_country = st.sidebar.selectbox(
    "Select Country or Entity",
    country_list,
    index=country_list.index('United States') if 'United States' in country_list else 0
)

# Filter 2: Year Range Selection (Slider)
year_range = st.sidebar.slider(
    "Select Year Range",
    min_value=min_year,
    max_value=max_year,
    value=(2000, max_year)
)

start_year, end_year = year_range

# --- Filter Data based on selections ---

if selected_country == 'Global':
    # Filter for the 'World' entity for global trends
    filtered_data = data[
        (data['country'] == 'World') & 
        (data['year'] >= start_year) & 
        (data['year'] <= end_year)
    ].copy()
    
    # Use the data for all countries for the Bar Chart/ranking
    country_ranking_data = data[
        (data['year'] == end_year) & 
        (~data['country'].isin(['World', 'International Transport', 'Oceania', 'Asia', 'Europe', 'Africa'])) # Exclude large aggregates
    ].sort_values(by='co2', ascending=False).head(10).copy()

else:
    # Filter for the selected country
    filtered_data = data[
        (data['country'] == selected_country) & 
        (data['year'] >= start_year) & 
        (data['year'] <= end_year)
    ].copy()

    # For ranking, use the data for all countries in the final year of the range
    country_ranking_data = data[
        (data['year'] == end_year) & 
        (~data['country'].isin(['World', 'International Transport', 'Oceania', 'Asia', 'Europe', 'Africa'])) 
    ].sort_values(by='co2', ascending=False).head(10).copy()


# --- Main Dashboard Title ---
st.title("🌍 Global CO₂ Emission Analysis")
st.markdown(f"*Viewing data for: {selected_country} from {start_year} to {end_year}*")


# --- Section 1: Data Summary (st.metric) ---
st.header("1. Key Metrics")

col1, col2, col3 = st.columns(3)

if not filtered_data.empty and 'co2' in filtered_data.columns:
    
    # Calculate key statistics for the selected country/range
    total_co2_emitted = filtered_data['co2'].sum()
    avg_annual_co2 = filtered_data['co2'].mean()
    max_emissions_year = filtered_data.loc[filtered_data['co2'].idxmax()]['year']
    max_emissions_value = filtered_data['co2'].max()
    
    with col1:
        st.metric(
            label=f"Total CO₂ Emissions ({start_year}-{end_year})", 
            value=f"{total_co2_emitted:,.0f} Mt", # Million tonnes
            delta=None
        )
        
    with col2:
        st.metric(
            label="Average Annual CO₂ Emissions", 
            value=f"{avg_annual_co2:,.0f} Mt",
            delta=None
        )

    with col3:
        st.metric(
            label="Year of Peak Emissions (in Range)", 
            value=f"{max_emissions_year}",
            delta=f"{max_emissions_value:,.0f} Mt",
            delta_color="off"
        )
else:
    st.warning("No data available for the selected filters.")

st.markdown("---")

# --- Section 2: Visualization 1 (Line Chart: Emissions Over Time) ---
st.header(f"2. Annual CO₂ Emissions Trend: {selected_country}")

if not filtered_data.empty:
    
    # Calculate the percentage change from the start year to the end year for the Delta metric
    if len(filtered_data) >= 2:
        start_emission = filtered_data.iloc[0]['co2']
        end_emission = filtered_data.iloc[-1]['co2']
        
        if start_emission != 0:
            change_percent = ((end_emission - start_emission) / start_emission) * 100
        else:
            change_percent = 0
            
        st.metric(
            label=f"Change from {start_year} to {end_year}",
            value=f"{end_emission:,.0f} Mt",
            delta=f"{change_percent:.1f}%"
        )

    # Plot the annual CO2 emissions
    fig_line = px.line(
        filtered_data, 
        x='year', 
        y='co2', 
        title=f'Annual CO₂ Emissions ({selected_country})',
        labels={'co2': 'Annual CO₂ Emissions (Million Tonnes)', 'year': 'Year'},
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    fig_line.update_traces(mode='lines+markers')
    fig_line.update_layout(xaxis_title="Year", yaxis_title="CO₂ Emissions (Million Tonnes)")
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Please select a valid country and year range to view the trend.")

st.markdown("---")


# --- Section 3: Visualization 2 (Bar Chart: Top 10 Emitters) ---
st.header(f"3. Top 10 CO₂ Emitters in {end_year}")

if not country_ranking_data.empty:
    
    # Plot the top 10 countries by CO2 emission in the selected end year
    fig_bar = px.bar(
        country_ranking_data,
        x='country',
        y='co2',
        color='co2',
        color_continuous_scale=px.colors.sequential.Reds,
        labels={'co2': 'CO₂ Emissions (Million Tonnes)', 'country': 'Country'},
        text_auto=True,
        title=f'Top 10 Countries by Annual CO₂ Emissions in {end_year}'
    )
    fig_bar.update_layout(
        xaxis_title="Country", 
        yaxis_title="CO₂ Emissions (Million Tonnes)",
        xaxis={'categoryorder':'total descending'}
    )
    fig_bar.update_traces(texttemplate='%{text:.2s} Mt', textposition='outside')
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.info(f"No ranking data available for the year {end_year}.")
    
st.markdown("---")

# --- Section 4: Raw Data (st.dataframe) ---
st.header("4. Filtered Raw Data Preview")
st.dataframe(filtered_data[['country', 'year', 'co2', 'co2_per_capita', 'population']].head(20), use_container_width=True)

st.sidebar.caption("Data Source: Our World in Data (Global Carbon Project)")