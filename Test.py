import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from Aqi_Utils import (calculate_aqi_status, get_persona_config, 
                       load_and_clean_data, generate_ml_forecast, 
                       get_user_location, generate_text_explanation, estimate_aqi_at_gps)
from solutions_engine import generate_actionable_responses

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="EcoGuard Pro | AI Air Monitor", page_icon="🍃", layout="wide")

st.markdown("""
<style>
    .metric-card { 
        background-color: #1E1E1E; border: 1px solid #444; border-radius: 12px; 
        padding: 15px; text-align: center; margin-bottom: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
    }
    div[data-testid="stMetricValue"] { font-size: 1.4rem !important; }
    
    .explanation-box { 
        background-color: #262730; border-left: 5px solid #00CC96; 
        padding: 15px; border-radius: 5px; margin-bottom: 20px; 
    }
    .stDownloadButton > button { width: 100%; border-color: #00CC96; color: #00CC96; }
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR CONTROLS ---
st.sidebar.title("🍃 EcoGuard Pro")
page = st.sidebar.radio("Navigation", ["🖥️ Live Dashboard", "🔮 AI Prediction", "🗺️ Heatmap & Location"])
st.sidebar.markdown("---")

st.sidebar.header("⚙️ Settings")
selected_persona = st.sidebar.selectbox("Select Persona", 
    ["Healthy Adult", "Elderly", "Child/Infant", "Athlete (Outdoor)", "Respiratory Patient"],
    help="Adjusts risk analysis based on health profile.")

uploaded_file = st.sidebar.file_uploader("Data Source", type=['csv'])
DEFAULT_PATH = r"C:\Users\ankit\OneDrive\Documents\Personal\Repls\Complete code\Random Python\AqiMonitor\Resource Files\Mumbai_Data.csv"

# --- 3. DATA LOADING ---
df = None
if uploaded_file: df = load_and_clean_data(uploaded_file)
else:
    df = load_and_clean_data(DEFAULT_PATH)
    if isinstance(df, str) or df is None:
        dates = pd.date_range(start='2023-01-01', periods=100, freq='h')
        pm = 80 + 40 * np.sin(np.linspace(0, 8*np.pi, 100)) + np.random.normal(0, 5, 100)
        df = pd.DataFrame({'timestamp': dates, 'city': 'Mumbai', 'pm25': np.abs(pm), 
                           'pm10': np.abs(pm * 1.5), 'temperature': 30, 'humidity': 50, 
                           'lat': 19.07, 'lon': 72.87})
        st.sidebar.warning("⚠️ Using DEMO DATA")
if isinstance(df, str): st.error(df); st.stop()

# --- 4. LOCATION INTELLIGENCE ---
available_locations = sorted(df['city'].unique().tolist())

if st.sidebar.button("📍 Locate Me (GPS)"):
    user_lat, user_lon = get_user_location()
    if user_lat:
        # Interpolation Logic
        estimated_aqi = estimate_aqi_at_gps(user_lat, user_lon, df)
        st.sidebar.success(f"Hyper-Local AQI Estimate: {estimated_aqi:.1f}")
        
        # Find Nearest Station
        locs = df.groupby('city')[['lat', 'lon']].mean().reset_index()
        locs['dist'] = np.sqrt((locs['lat']-user_lat)**2 + (locs['lon']-user_lon)**2)
        nearest = locs.sort_values('dist').iloc[0]['city']
        st.session_state['selected_loc'] = nearest
        st.sidebar.info(f"Nearest Sensor: {nearest}")
    else:
        st.sidebar.error("GPS Failed. Check internet connection.")

# Ensure valid selection
if 'selected_loc' not in st.session_state or st.session_state['selected_loc'] not in available_locations:
    st.session_state['selected_loc'] = available_locations[0]

selected_location = st.sidebar.selectbox("Monitored Station", available_locations, 
                                         index=available_locations.index(st.session_state['selected_loc']))
st.session_state['selected_loc'] = selected_location

# --- 5. DATA FILTERING ---
filtered_df = df[df['city'] == selected_location].sort_values('timestamp')
latest = filtered_df.iloc[-1]
pm25 = latest.get('pm25', 0)
status, color = calculate_aqi_status(pm25, selected_persona)
persona_config = get_persona_config(selected_persona)

# Generate Forecast horizons for explainability & smart actions
forecast_horizon = generate_ml_forecast(filtered_df, periods=12)
ml_forecast_df = forecast_horizon.head(1) if not forecast_horizon.empty else pd.DataFrame()
smart_actions = generate_actionable_responses(selected_location, filtered_df, forecast_horizon)

# Sidebar Smart City summary
st.sidebar.subheader("🚦 Smart City Actions")
severity_to_fn = {
    'error': st.sidebar.error,
    'warning': st.sidebar.warning,
    'success': st.sidebar.success,
    'info': st.sidebar.info
}
if smart_actions:
    for action in smart_actions:
        render_fn = severity_to_fn.get(action.severity, st.sidebar.info)
        render_fn(f"**{action.title}**\n{action.message}")
else:
    st.sidebar.success("Systems stable. No reroutes or mitigations required.")

# Download Report
st.sidebar.markdown("---")
@st.cache_data
def convert_df(df): return df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button("📥 Download Analysis", convert_df(filtered_df), f"{selected_location}_report.csv", "text/csv")

# ==========================================
#           WINDOW 1: LIVE DASHBOARD
# ==========================================
if page == "🖥️ Live Dashboard":
    st.title(f"🌍 {selected_location}")
    
    # AI Explanation Block
    explanation = generate_text_explanation(pm25, filtered_df, ml_forecast_df, 
                                            latest.get('humidity', None), latest.get('temperature', None))
    st.markdown(f"""<div class="explanation-box">
        <h4>EcoGuard AI Analysis</h4>
        <p style="font-size:1.1em">{explanation}</p>
    </div>""", unsafe_allow_html=True)

    col_g, col_rec = st.columns([1, 2])
    with col_g:
        limits = persona_config["thresholds"]
        gauge_max = max(150, limits[-1] * 1.2)
        fig_gauge = go.Figure(go.Indicator(mode="gauge+number", value=pm25, 
            title={'text': f"AQI (PM2.5)<br><span style='font-size:0.6em'>{selected_persona}</span>"},
            gauge={'axis': {'range': [None, gauge_max]}, 'bar': {'color': "white"}, 'steps': [
                {'range': [0, limits[0]], 'color': "#00e400"},
                {'range': [limits[0], limits[1]], 'color': "#ffff00"},
                {'range': [limits[1], limits[2]], 'color': "#ff7e00"},
                {'range': [limits[2], limits[3]], 'color': "#ff0000"},
                {'range': [limits[3], limits[4]], 'color': "#8f3f97"},
                {'range': [limits[4], gauge_max], 'color': "#7e0023"}], 
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': pm25}}))
        fig_gauge.update_layout(height=280, margin=dict(l=20,r=20,t=40,b=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    with col_rec:
        st.info(f"**Health Advice:** {persona_config['advice_by_status'].get(status, '')}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Temperature", f"{latest.get('temperature',0):.1f} °C")
        c2.metric("Humidity", f"{latest.get('humidity',0):.1f} %")
        pm10_val = latest.get('pm10', latest.get('pm25', 0) * 1.5)
        c3.metric("PM 10", f"{pm10_val:.1f}")
    
    st.plotly_chart(px.area(filtered_df.tail(48), x='timestamp', y='pm25', title="48-Hour Trend Analysis", template="plotly_dark"), use_container_width=True)

# ==========================================
#           WINDOW 2: AI PREDICTION (ML)
# ==========================================
elif page == "🔮 AI Prediction":
    st.title("🔮 Temporal Prediction Engine")
    st.markdown("""
    **Methodology:** Random Forest Regression (Recursive Multi-step)
    * **Features:** Hour of Day, Day of Week, Lag-1 (T-1h), Lag-24 (T-24h)
    * **Goal:** Predict AQI trends 12 hours ahead.
    """)
    
    with st.spinner("Training Model on Historical Data..."):
        full_forecast_df = forecast_horizon.copy()
    
    if not full_forecast_df.empty:
        combined = pd.concat([filtered_df.tail(36), full_forecast_df], ignore_index=True)
        fig = px.line(combined, x='timestamp', y='pm25', color='type', 
                      color_discrete_map={"Historical": "gray", "Forecast": "#00CC96"}, markers=True)
        
        # Add Dynamic Threshold Line based on Persona
        limit = persona_config["thresholds"][2]
        fig.add_hline(y=limit, line_dash="dot", line_color="red", annotation_text=f"Risk Threshold ({selected_persona})")
        
        fig.update_layout(template="plotly_dark", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("View Prediction Data"):
            st.dataframe(full_forecast_df, use_container_width=True)
    else: st.error("Insufficient data for ML training (>24 rows needed).")

# ==========================================
#           WINDOW 3: HEATMAP
# ==========================================
elif page == "🗺️ Heatmap & Location":
    st.title("🗺️ Hyper-Local Spatial Intelligence")
    
    center_lat = latest.get('lat', 28.61)
    center_lon = latest.get('lon', 77.20)
    
    st.subheader(f"📍 Target: {selected_location}")
    c1, c2 = st.columns(2)
    c1.metric("Latitude", f"{center_lat:.4f}")
    c2.metric("Longitude", f"{center_lon:.4f}")

    st.divider()
    st.subheader("🌍 Regional Pollution Heatmap")
    
    latest_all = df.groupby('city').last().reset_index()
    
    # RdYlGn_r -> Green (Low) to Red (High)
    fig = px.density_mapbox(latest_all, lat='lat', lon='lon', z='pm25', 
                            radius=40, center=dict(lat=center_lat, lon=center_lon), 
                            zoom=10, mapbox_style="carto-darkmatter",
                            color_continuous_scale="RdYlGn_r", 
                            title=f"Pollution Density around {selected_location}")
    
    # Add User/Station Marker
    fig.add_scattermapbox(lat=[center_lat], lon=[center_lon], mode='markers+text',
                          marker=dict(size=12, color='white', symbol='circle'),
                          text=["TARGET"], textposition="top center")
    
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
#      ACTIONABLE RESPONSE SYSTEM (GLOBAL)
# ==========================================
st.markdown("## 🛡️ Actionable Response System")
main_severity_map = {
    'error': st.error,
    'warning': st.warning,
    'success': st.success,
    'info': st.info
}
if smart_actions:
    for action in smart_actions:
        render_fn = main_severity_map.get(action.severity, st.info)
        render_fn(f"**{action.title}**\n{action.message}")
else:
    st.success("No immediate interventions required. Continue routine monitoring.")