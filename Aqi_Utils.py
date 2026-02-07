import pandas as pd
import numpy as np
import geocoder
from datetime import timedelta
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor

# --- CONFIG: CITY COORDINATES ---
CITY_COORDS = {
    "New Delhi": (28.6139, 77.2090), "Mumbai": (19.0760, 72.8777),
    "Bengaluru": (12.9716, 77.5946), "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639), "Hyderabad": (17.3850, 78.4867),
    "Pune": (18.5204, 73.8567), "Ahmedabad": (23.0225, 72.5714),
    "Jaipur": (26.9124, 75.7873), "Lucknow": (26.8467, 80.9462)
}

# --- 1. GEOSPATIAL ENGINE ---
def get_user_location():
    """Returns approximate user (lat, lon) via IP."""
    try:
        g = geocoder.ip('me')
        if g.latlng: return g.latlng[0], g.latlng[1]
    except: pass
    return None, None

def estimate_aqi_at_gps(user_lat, user_lon, df):
    """
    Hyper-Local Intelligence: Uses Inverse Distance Weighting (IDW)
    to estimate pollution at the exact user GPS location based on nearby stations.
    """
    try:
        latest_data = df.groupby('city').last().reset_index()
        # Calculate distance to all stations
        latest_data['dist'] = np.sqrt((latest_data['lat'] - user_lat)**2 + (latest_data['lon'] - user_lon)**2)
        
        # If very close to a station, return that station's value
        if latest_data['dist'].min() < 0.001: 
            return latest_data.sort_values('dist').iloc[0]['pm25']
        
        # Otherwise, interpolate using top 3 nearest stations
        nearest = latest_data.sort_values('dist').head(3)
        weights = 1 / nearest['dist'] # Closer stations get higher weight
        estimated_val = (nearest['pm25'] * weights).sum() / weights.sum()
        
        return estimated_val
    except: return 0

# --- 2. HEALTH RISK ENGINE (PERSONAS) ---
# WHO 2021 Air Quality Guidelines (PM2.5, 24-hour): 15 µg/m³
# Interim targets: 25, 37.5, 50, 75 µg/m³
WHO_PM25_24H_THRESHOLDS = [15, 25, 37.5, 50, 75]

def get_persona_config(persona):
    advice = {
        "Healthy Adult": {
            "Within WHO Guideline": "Air quality meets WHO 24-hour guidance. Normal outdoor activity is appropriate.",
            "Above WHO Guideline": "Consider reducing prolonged outdoor exertion, especially during peaks.",
            "High": "Limit extended outdoor activity; prefer low-intensity or indoor alternatives.",
            "Very High": "Avoid prolonged outdoor activity; keep windows closed during peak hours.",
            "Extremely High": "Stay indoors with air filtration when possible; avoid outdoor exercise.",
            "Severe": "Avoid outdoor exposure; use well-fitted masks if you must go out."
        },
        "Elderly": {
            "Within WHO Guideline": "Air quality meets WHO guidance, but monitor symptoms and keep activities moderate.",
            "Above WHO Guideline": "Reduce time outdoors; avoid heavy exertion.",
            "High": "Prefer indoor activities; keep medications accessible.",
            "Very High": "Stay indoors; use air filtration if available.",
            "Extremely High": "Avoid outdoor exposure; consider telehealth if symptoms worsen.",
            "Severe": "Remain indoors; seek medical advice if breathing symptoms appear."
        },
        "Child/Infant": {
            "Within WHO Guideline": "Air quality meets WHO guidance. Outdoor play is okay with supervision.",
            "Above WHO Guideline": "Limit prolonged outdoor play, especially near traffic.",
            "High": "Move play indoors; keep windows closed during peaks.",
            "Very High": "Avoid outdoor play; use indoor air filtration if possible.",
            "Extremely High": "Keep children indoors; avoid intense activity.",
            "Severe": "Avoid outdoor exposure; seek care if wheezing or coughing increases."
        },
        "Athlete (Outdoor)": {
            "Within WHO Guideline": "Air quality meets WHO guidance. Normal training is fine.",
            "Above WHO Guideline": "Reduce training intensity and duration; avoid high-traffic routes.",
            "High": "Move training indoors or switch to low-intensity sessions.",
            "Very High": "Avoid outdoor training; indoor alternatives recommended.",
            "Extremely High": "Postpone outdoor sessions; prioritize recovery indoors.",
            "Severe": "Do not train outdoors; avoid exposure."
        },
        "Respiratory Patient": {
            "Within WHO Guideline": "Air quality meets WHO guidance, but keep inhalers accessible.",
            "Above WHO Guideline": "Limit outdoor exposure; monitor breathing closely.",
            "High": "Avoid outdoor exertion; use air filtration if available.",
            "Very High": "Stay indoors; follow your action plan and medications.",
            "Extremely High": "Avoid outdoor exposure; consider medical advice if symptoms worsen.",
            "Severe": "Remain indoors; seek medical care if breathing is difficult."
        }
    }

    return {
        "thresholds": WHO_PM25_24H_THRESHOLDS,
        "advice_by_status": advice.get(persona, advice["Healthy Adult"]) 
    }

def calculate_aqi_status(pm25_value, persona="Healthy Adult"):
    limits = WHO_PM25_24H_THRESHOLDS
    if pm25_value <= limits[0]: return "Within WHO Guideline", "#00e400" # Green
    elif pm25_value <= limits[1]: return "Above WHO Guideline", "#ffff00" # Yellow
    elif pm25_value <= limits[2]: return "High", "#ff7e00" # Orange
    elif pm25_value <= limits[3]: return "Very High", "#ff0000" # Red
    elif pm25_value <= limits[4]: return "Extremely High", "#8f3f97" # Purple
    else: return "Severe", "#7e0023" # Maroon

# --- 3. EXPLAINABILITY ENGINE (NARRATIVE AI) ---
def generate_text_explanation(current_pm25, history_df, forecast_df, humidity, temp):
    """
    Analyzes data context to generate a human-readable "Thinking" analysis.
    """
    analysis = []
    
    # A. Contextual Analysis (Vs WHO 24-hour guideline & daily average)
    who_guideline = WHO_PM25_24H_THRESHOLDS[0]
    if current_pm25 <= who_guideline:
        analysis.append("✅ Within WHO 24-hour guideline for PM2.5 (15 µg/m³). \n")
    else:
        analysis.append("⚠️ Above WHO 24-hour guideline for PM2.5 (15 µg/m³). \n")

    # B. Contextual Analysis (Vs Daily Average)
    avg_24h = history_df.tail(24)['pm25'].mean()
    if current_pm25 > avg_24h * 1.25:
        analysis.append(f"⚠️ Acute Spike: Current PM2.5 levels ({current_pm25:.0f}) are 25% higher than today's average. \n")
    elif current_pm25 < avg_24h * 0.75:
        analysis.append(f"✅ Air Clearing: Pollution levels are currently lower than the daily average. \n")
    else:
        analysis.append("Current air quality is stable and consistent with daily trends. \n")
    # C. Trend Analysis (Rate of Change)
    if len(history_df) >= 2:
        change = current_pm25 - history_df.iloc[-2]['pm25']
        if change > 15: analysis.append("Pollutants are accumulating rapidly (High Rate of Change). \n")
        elif change < -15: analysis.append("Atmospheric dispersion is active, leading to a rapid improvement. \n")
    
    # D. Environmental Factors
    factors = []
    # Check Time of Day
    hour = history_df.iloc[-1]['timestamp'].hour
    if 8 <= hour <= 11 or 18 <= hour <= 21: factors.append("vehicular emissions during peak hours. \n")
    
    # Check Weather
    if humidity and humidity > 75: factors.append("high humidity trapping particulates. \n")
    if temp and temp < 15: factors.append("low temperature inversion. \n")
    
    if factors:
        analysis.append(f"Primary drivers include {' and '.join(factors)}. \n")

    # E. Forecast Insight
    if not forecast_df.empty:
        next_val = forecast_df.iloc[0]['pm25']
        if next_val > current_pm25:
            analysis.append("📈 Outlook: The AI model predicts conditions will worsen over the next hour. \n")
        else:
            analysis.append("📉 Outlook: The AI model predicts a gradual improvement. \n")

    return " ".join(analysis)

# --- 4. TEMPORAL PREDICTION ENGINE (RANDOM FOREST) ---
def generate_ml_forecast(df, periods=12):
    """Recursive multi-step PM2.5 forecast with enriched temporal features and boosted trees."""
    try:
        if df.empty or len(df) < 36: return pd.DataFrame()

        work_df = df[['timestamp', 'pm25']].copy()
        work_df['timestamp'] = pd.to_datetime(work_df['timestamp'], errors='coerce', format='mixed')
        work_df['pm25'] = pd.to_numeric(work_df['pm25'], errors='coerce')
        work_df = work_df.dropna(subset=['timestamp', 'pm25']).sort_values('timestamp')
        if work_df.empty: return pd.DataFrame()

        engineered = work_df.copy()
        engineered['hour'] = engineered['timestamp'].dt.hour
        engineered['dayofweek'] = engineered['timestamp'].dt.dayofweek
        engineered['sin_hour'] = np.sin(2 * np.pi * engineered['hour'] / 24)
        engineered['cos_hour'] = np.cos(2 * np.pi * engineered['hour'] / 24)
        engineered['sin_dow'] = np.sin(2 * np.pi * engineered['dayofweek'] / 7)
        engineered['cos_dow'] = np.cos(2 * np.pi * engineered['dayofweek'] / 7)

        for lag in [1, 3, 6, 12, 24]:
            engineered[f'lag_{lag}'] = engineered['pm25'].shift(lag)

        engineered['rolling_mean_6'] = engineered['pm25'].rolling(window=6).mean()
        engineered['rolling_mean_24'] = engineered['pm25'].rolling(window=24).mean()
        engineered['rolling_std_24'] = engineered['pm25'].rolling(window=24).std().fillna(0)

        feature_cols = [
            'hour', 'dayofweek', 'sin_hour', 'cos_hour', 'sin_dow', 'cos_dow',
            'lag_1', 'lag_3', 'lag_6', 'lag_12', 'lag_24',
            'rolling_mean_6', 'rolling_mean_24', 'rolling_std_24'
        ]

        model_df = engineered.dropna(subset=feature_cols)
        if model_df.empty: return pd.DataFrame()

        X = model_df[feature_cols]
        y = model_df['pm25']

        try:
            model = HistGradientBoostingRegressor(
                max_depth=6,
                max_iter=500,
                learning_rate=0.08,
                l2_regularization=0.01,
                random_state=42
            )
        except Exception:
            model = RandomForestRegressor(
                n_estimators=350,
                max_depth=14,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )

        model.fit(X, y)

        history_vals = model_df['pm25'].tolist()
        current_time = model_df.iloc[-1]['timestamp']

        city = df.iloc[-1]['city'] if 'city' in df else "Unknown"
        lat = df.iloc[-1]['lat'] if 'lat' in df else 0
        lon = df.iloc[-1]['lon'] if 'lon' in df else 0

        future_preds = []

        def get_lag(history, steps):
            if not history: return 0
            return history[-steps] if len(history) >= steps else history[0]

        def get_tail(history, window):
            return history[-window:] if len(history) >= window else history

        for step in range(1, periods + 1):
            next_time = current_time + timedelta(hours=step)
            tail6 = get_tail(history_vals, 6)
            tail24 = get_tail(history_vals, 24)

            feature_row = {
                'hour': next_time.hour,
                'dayofweek': next_time.dayofweek,
                'sin_hour': np.sin(2 * np.pi * next_time.hour / 24),
                'cos_hour': np.cos(2 * np.pi * next_time.hour / 24),
                'sin_dow': np.sin(2 * np.pi * next_time.dayofweek / 7),
                'cos_dow': np.cos(2 * np.pi * next_time.dayofweek / 7),
                'lag_1': get_lag(history_vals, 1),
                'lag_3': get_lag(history_vals, 3),
                'lag_6': get_lag(history_vals, 6),
                'lag_12': get_lag(history_vals, 12),
                'lag_24': get_lag(history_vals, 24),
                'rolling_mean_6': float(np.mean(tail6)),
                'rolling_mean_24': float(np.mean(tail24)),
                'rolling_std_24': float(np.std(tail24))
            }

            feature_vector = pd.DataFrame([feature_row])[feature_cols]
            model_pred = model.predict(feature_vector)[0]
            seasonal_baseline = get_lag(history_vals, 24)
            blended_pred = 0.7 * model_pred + 0.3 * seasonal_baseline
            forecast_value = max(5.0, blended_pred)

            history_vals.append(forecast_value)

            future_preds.append({
                'timestamp': next_time,
                'pm25': forecast_value,
                'pm10': max(10.0, forecast_value * 1.5),
                'city': city,
                'lat': lat,
                'lon': lon,
                'type': 'Forecast'
            })

        return pd.DataFrame(future_preds)
    except Exception as e:
        print(f"ML Error: {e}")
        return pd.DataFrame()

# --- 5. ROBUST DATA LOADER ---
def load_and_clean_data(filepath):
    try:
        df = pd.read_csv(filepath)
        # Normalize headers
        df.columns = df.columns.str.strip().str.lower().str.replace('.', '', regex=False).str.replace(' ', '').str.replace('_', '')
        
        # Smart Column Mapping
        for col in df.columns:
            if 'temp' in col: df.rename(columns={col: 'temperature'}, inplace=True)
            elif 'hum' in col or 'rh' == col: df.rename(columns={col: 'humidity'}, inplace=True)
            elif 'pm10' in col: df.rename(columns={col: 'pm10'}, inplace=True)
            elif 'pm25' in col: df.rename(columns={col: 'pm25'}, inplace=True)

        col_map = {'date': 'timestamp', 'time': 'timestamp', 'datetime': 'timestamp'}
        df.rename(columns=col_map, inplace=True)
        
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', format='mixed')
            df = df.dropna(subset=['timestamp']).sort_values('timestamp')
        else: return "Error: timestamp column missing."

        # Smart Location Detection
        possible_cols = ['city', 'location', 'station', 'site', 'place', 'stationid']
        found_col = None
        for col in possible_cols:
            if col in df.columns: found_col = col; break
        if found_col: df.rename(columns={found_col: 'city'}, inplace=True)
        else: df['city'] = "Main Station"

        # Handle Missing Values (Interpolation)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].interpolate(method='linear').ffill().bfill()
        
        # Map Coordinates
        if 'lat' not in df.columns or 'lon' not in df.columns:
            df['lat'] = df['city'].map(lambda x: CITY_COORDS.get(x, (28.61, 77.20))[0]) + np.random.uniform(-0.01, 0.01, len(df))
            df['lon'] = df['city'].map(lambda x: CITY_COORDS.get(x, (28.61, 77.20))[1]) + np.random.uniform(-0.01, 0.01, len(df))

        # Downsample large datasets
        if len(df) > 5000:
            df = df.groupby(['city', pd.Grouper(key='timestamp', freq='1h')])[numeric_cols].mean().reset_index()

        df['type'] = 'Historical'
        return df
    except Exception as e: return str(e)    