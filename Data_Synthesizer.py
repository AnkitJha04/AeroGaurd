import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_final_15yr_data():
    print("🏭 Initializing 15-YEAR MASSIVE Mumbai Simulator...")
    print("   -> Target: 2011-2026 (15 Years)")
    print("   -> Scope: 102 Locations")
    print("   -> Physics: Fixed & Validated")

    # 1. FULL 102 LOCATIONS LIST
    # (Name, Lat, Lon, Ind_Score, Traf_Score)
    locations = [
        # SOUTH MUMBAI
        ("Colaba", 18.9067, 72.8147, 1.0, 3.0), ("Cuffe Parade", 18.9142, 72.8153, 1.0, 3.0),
        ("Nariman Point", 18.9260, 72.8225, 1.0, 4.0), ("Churchgate", 18.9322, 72.8264, 1.0, 4.5),
        ("Fort", 18.9345, 72.8371, 1.2, 4.5), ("Marine Lines", 18.9447, 72.8244, 1.0, 3.5),
        ("Kalbadevi", 18.9507, 72.8295, 2.0, 5.0), ("Bhuleshwar", 18.9535, 72.8290, 2.5, 5.0),
        ("Girgaon", 18.9566, 72.8195, 1.5, 4.0), ("Malabar Hill", 18.9548, 72.7985, 1.0, 2.0),
        ("Breach Candy", 18.9686, 72.8051, 1.0, 3.0), ("Tardeo", 18.9702, 72.8139, 1.5, 4.0),
        ("Mumbai Central", 18.9697, 72.8194, 2.0, 5.0), ("Byculla", 18.9780, 72.8340, 2.5, 4.5),
        ("Mazgaon", 18.9678, 72.8465, 3.0, 3.5), ("Mahalakshmi", 18.9827, 72.8236, 1.5, 4.0),
        ("Worli", 19.0178, 72.8194, 1.5, 3.5), ("Lower Parel", 18.9953, 72.8315, 3.0, 5.0),
        ("Prabhadevi", 19.0166, 72.8295, 1.5, 3.5), ("Dadar West", 19.0207, 72.8422, 1.5, 5.0),
        ("Dadar East", 19.0178, 72.8473, 1.5, 5.0), ("Wadala", 19.0216, 72.8646, 3.5, 4.0),
        ("Sion", 19.0390, 72.8619, 3.0, 5.0), ("Matunga", 19.0269, 72.8553, 1.0, 3.0),
        ("Mahim", 19.0354, 72.8402, 2.0, 4.0), ("Dharavi", 19.0380, 72.8538, 4.0, 3.5),

        # WESTERN SUBURBS
        ("Bandra West", 19.0607, 72.8362, 1.2, 4.5), ("Bandra East", 19.0600, 72.8450, 2.0, 5.0),
        ("Khar", 19.0700, 72.8338, 1.0, 3.5), ("Santacruz West", 19.0843, 72.8360, 1.0, 4.0),
        ("Santacruz East", 19.0805, 72.8569, 1.5, 4.5), ("Vile Parle West", 19.1023, 72.8397, 1.2, 4.0),
        ("Vile Parle East", 19.0984, 72.8528, 1.5, 4.5), ("Juhu", 19.1075, 72.8263, 1.0, 3.0),
        ("Andheri West", 19.1136, 72.8338, 2.0, 5.0), ("Andheri East", 19.1155, 72.8643, 4.0, 5.0),
        ("Versova", 19.1351, 72.8146, 1.0, 3.0), ("Jogeshwari West", 19.1299, 72.8408, 2.5, 4.5),
        ("Jogeshwari East", 19.1362, 72.8614, 3.0, 4.5), ("Goregaon West", 19.1663, 72.8423, 2.0, 4.0),
        ("Goregaon East", 19.1688, 72.8624, 2.5, 4.5), ("Malad West", 19.1874, 72.8285, 2.0, 4.5),
        ("Malad East", 19.1860, 72.8563, 3.0, 5.0), ("Kandivali West", 19.2065, 72.8340, 2.0, 4.0),
        ("Kandivali East", 19.2104, 72.8687, 3.0, 4.5), ("Borivali West", 19.2274, 72.8428, 1.5, 4.0),
        ("Borivali East", 19.2298, 72.8643, 2.0, 4.5), ("Dahisar", 19.2494, 72.8596, 2.0, 4.0),

        # EASTERN SUBURBS
        ("Kurla West", 19.0728, 72.8715, 3.5, 5.0), ("Kurla East", 19.0649, 72.8833, 4.0, 4.5),
        ("Vidyavihar", 19.0792, 72.8973, 3.0, 3.5), ("Ghatkopar West", 19.0898, 72.8986, 3.0, 4.5),
        ("Ghatkopar East", 19.0860, 72.9089, 3.0, 4.0), ("Vikhroli West", 19.1118, 72.9112, 3.5, 4.0),
        ("Vikhroli East", 19.1051, 72.9312, 3.0, 4.0), ("Kanjurmarg", 19.1256, 72.9356, 4.0, 4.5),
        ("Bhandup West", 19.1436, 72.9317, 3.5, 4.0), ("Nahur", 19.1554, 72.9436, 3.0, 3.5),
        ("Mulund West", 19.1726, 72.9425, 2.0, 3.5), ("Mulund East", 19.1751, 72.9642, 2.5, 3.0),
        ("Powai", 19.1176, 72.9060, 1.5, 4.0), ("Chandivali", 19.1102, 72.8967, 3.0, 4.0),
        ("Mankhurd", 19.0478, 72.9333, 5.0, 4.0), ("Govandi", 19.0558, 72.9157, 5.0, 4.0),
        ("Chembur", 19.0522, 72.9005, 4.5, 4.5), ("Trombay", 19.0163, 72.9189, 5.0, 3.0),

        # THANE & BEYOND
        ("Thane West", 19.2183, 72.9781, 2.5, 4.5), ("Thane East", 19.2155, 72.9868, 3.0, 4.0),
        ("Ghodbunder Road", 19.2740, 72.9558, 2.0, 4.5), ("Kalwa", 19.1986, 72.9943, 3.5, 4.0),
        ("Mumbra", 19.1738, 73.0232, 4.0, 4.0), ("Diva", 19.1887, 73.0431, 3.5, 3.5),
        ("Dombivli West", 19.2184, 73.0867, 3.5, 4.5), ("Dombivli East", 19.2094, 73.0939, 3.5, 4.5),
        ("Kalyan West", 19.2403, 73.1305, 3.5, 5.0), ("Kalyan East", 19.2355, 73.1436, 3.5, 4.5),
        ("Ulhasnagar", 19.2215, 73.1645, 4.0, 4.0), ("Ambarnath", 19.1920, 73.1982, 4.5, 3.5),
        ("Badlapur", 19.1559, 73.2639, 3.0, 3.0), ("Bhiwandi", 19.2969, 73.0588, 5.0, 5.0),

        # NAVI MUMBAI
        ("Airoli", 19.1590, 72.9986, 3.0, 4.0), ("Rabale", 19.1436, 73.0033, 4.5, 3.5),
        ("Ghansoli", 19.1254, 73.0046, 4.0, 3.5), ("Kopar Khairane", 19.1027, 73.0031, 3.5, 3.5),
        ("Vashi", 19.0748, 72.9978, 2.0, 4.5), ("Sanpada", 19.0628, 73.0135, 1.5, 3.5),
        ("Juinagar", 19.0537, 73.0167, 2.0, 3.5), ("Nerul", 19.0330, 73.0297, 1.5, 3.5),
        ("Seawoods", 19.0189, 73.0210, 1.0, 3.0), ("Belapur", 18.9894, 73.0366, 1.5, 3.5),
        ("Kharghar", 19.0237, 73.0679, 1.5, 3.5), ("Panvel", 18.9894, 73.1178, 2.5, 4.5),
        ("Kalamboli", 19.0305, 73.0970, 4.0, 4.0), ("Taloja", 19.0615, 73.1077, 5.0, 3.5),
        ("Uran", 18.8778, 72.9366, 3.5, 3.0), ("Nhava Sheva", 18.9515, 72.9641, 4.5, 5.0),

        # MIRA BHAYANDAR & VASAI
        ("Mira Road", 19.2842, 72.8687, 2.0, 4.5), ("Bhayandar West", 19.2938, 72.8466, 2.5, 4.0),
        ("Bhayandar East", 19.3074, 72.8596, 2.5, 4.0), ("Naigaon", 19.3524, 72.8475, 1.5, 3.0),
        ("Vasai West", 19.3664, 72.8155, 2.0, 3.5), ("Vasai East", 19.3917, 72.8576, 3.0, 4.0),
        ("Nalasopara West", 19.4184, 72.8021, 2.5, 4.0), ("Nalasopara East", 19.4215, 72.8273, 2.5, 4.0),
        ("Virar West", 19.4564, 72.7955, 2.0, 3.5), ("Virar East", 19.4678, 72.8184, 2.5, 3.5),
        ("Palghar", 19.6936, 72.7655, 2.5, 3.0), ("Boisar", 19.7969, 72.7452, 5.0, 3.0)
    ]

    # 2. TIME SETUP (15 YEARS)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*15)
    
    # Generate range with 'h' frequency (Standard pandas)
    dates = pd.date_range(start=start_date, end=end_date, freq='h')
    
    n = len(dates)
    hours = dates.hour.values
    months = dates.month.values
    years = dates.year.values
    
    print(f"   -> Calculated {n:,} rows per location.")
    print("   -> Applying Corrected Physics Models...")

    # 3. GLOBAL PHYSICS VECTORS (With Correct Masking)
    
    # Seasons Masks
    is_winter = (months == 12) | (months == 1) | (months == 2)
    is_summer = (months >= 3) & (months <= 5)
    is_monsoon = (months >= 6) & (months <= 9)
    is_october = (months == 10)

    # Temperature (Coastal Pattern)
    # FIX: Slicing the input 'hours' to match the boolean mask size
    base_temp = np.zeros(n)
    base_temp[is_winter] = 22 + 6 * np.sin((hours[is_winter]-9)/24 * 2*np.pi)
    base_temp[is_summer] = 30 + 5 * np.sin((hours[is_summer]-9)/24 * 2*np.pi)
    base_temp[is_monsoon] = 27 + 2 * np.sin((hours[is_monsoon]-9)/24 * 2*np.pi)
    base_temp[is_october] = 29 + 6 * np.sin((hours[is_october]-9)/24 * 2*np.pi)
    base_temp[base_temp == 0] = 28 
    
    temp = base_temp + np.random.normal(0, 1.5, n)

    # Humidity
    base_hum = np.zeros(n)
    base_hum[is_winter] = 60
    base_hum[is_summer] = 70
    base_hum[is_monsoon] = 90
    base_hum[is_october] = 72
    base_hum[base_hum == 0] = 65
    
    hum_cycle = -15 * np.sin((hours-9)/24 * 2*np.pi) 
    hum = base_hum + hum_cycle + np.random.normal(0, 5, n)
    hum = np.clip(hum, 25, 100)

    # Wind
    wind_cycle = 3 + 3 * np.sin((hours-14)/24 * 2*np.pi) 
    wind = wind_cycle + np.random.exponential(1.5, n)
    wind[is_monsoon] += 5.0 

    # Rain
    rain = np.zeros(n)
    rain_prob = np.random.rand(n)
    is_raining = is_monsoon & (rain_prob > 0.60)
    rain[is_raining] = np.random.exponential(12, np.sum(is_raining))
    
    # Urban Growth (15-Year Trend)
    year_factor = (years - years.min()) / (years.max() - years.min())
    urban_growth = 1.0 + (year_factor * 0.30) 

    all_dfs = []
    
    # 4. LOCATION SIMULATION
    counter = 0
    for name, lat, lon, ind_score, traf_score in locations:
        counter += 1
        print(f"   [{counter}/102] Simulating {name}...", end="\r")
        
        # Traffic Pattern
        traffic = np.ones(n) * 0.5
        is_weekday = dates.dayofweek < 5
        morning_rush = is_weekday & (hours >= 8) & (hours <= 11)
        evening_rush = is_weekday & (hours >= 17) & (hours <= 21)
        
        traffic[morning_rush] = 2.0 * traf_score
        traffic[evening_rush] = 2.2 * traf_score
        traffic[~is_weekday] *= 0.7 
        traffic *= urban_growth
        
        # Ventilation
        ventilation = (wind * 0.7) + (rain * 2.0) + 0.5
        
        # Inversion (Corrected Masking)
        inv_mask = is_winter & ((hours >= 23) | (hours <= 7))
        inversion = np.ones(n)
        inversion[inv_mask] = 2.0
        
        # Base Load
        base_load = 35 * ind_score * urban_growth
        
        # AQI Equation
        pm25 = (base_load + (traffic * 18)) * inversion / ventilation
        
        # Diwali Event (Loop Years)
        for y in np.unique(years):
            try:
                # Target Nov 12th as approx Diwali
                diwali_mask = (years == y) & (months == 11) & (dates.day == 12)
                if np.sum(diwali_mask) > 0:
                    pm25[diwali_mask] *= 6.0 
            except: pass

        # Random Fires
        if ind_score > 3.0:
            fire_prob = np.random.rand(n) < 0.0002 
            pm25[fire_prob] *= 5.0 

        # Noise & Clamp
        pm25 += np.random.normal(0, 5, n)
        pm25 = np.maximum(5, pm25)

        # Derived Pollutants
        pm10 = pm25 * np.random.uniform(1.8, 3.0, n)
        no2 = (12 * traffic) + np.random.normal(0, 3, n)
        so2 = (8 * ind_score) + np.random.normal(0, 2, n)
        
        # DataFrame Construction
        # Use float32 to save memory
        df_loc = pd.DataFrame({
            'timestamp': dates,
            'city': name,
            'lat': lat,
            'lon': lon,
            'pm25': np.round(pm25, 1).astype('float32'),
            'pm10': np.round(pm10, 1).astype('float32'),
            'no2': np.round(no2, 1).astype('float32'),
            'so2': np.round(so2, 1).astype('float32'),
            'temperature': np.round(temp, 1).astype('float32'),
            'humidity': np.round(hum, 0).astype('float32'),
            'wind_speed': np.round(wind, 1).astype('float32'),
            'precipitation': np.round(rain, 1).astype('float32')
        })
        all_dfs.append(df_loc)

    print("\n🔄 Merging Dataset (This may take a minute)...")
    final_df = pd.concat(all_dfs, ignore_index=True)
    
    # Save
    path = "C:\\Users\\ankit\\OneDrive\\Documents\\Personal\\Repls\\Complete code\\Random Python\\AqiMonitor\\Resource Files\\Mumbai_Data.csv"
    
    print(f"💾 Saving to CSV ({len(final_df)} rows)...")
    final_df.to_csv(path, index=False)
    print("✅ SUCCESS! 15-Year Dataset Generated.")
    print(f"   Path: {path}")

if __name__ == "__main__":
    generate_final_15yr_data()